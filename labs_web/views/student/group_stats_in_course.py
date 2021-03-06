from flask import render_template, abort
from flask.views import View
from flask_login import current_user, login_required
from labs_web.extensions import celery, cache, User, Course, Group, Report
from labs_web import app


class ReportsProcessor:
    def __init__(self, student: User, reports, max_reports: int):
        self.name = student.name
        self.reports = ['N/A' for i in range(max_reports)]
        self.sum = sum([i.report_mark for i in reports if i.report_mark])
        for i in reports:
            self.reports[i.report_num - 1] = i.report_mark if i.report_mark else 'N/C'

    def __repr__(self):
        return "Reports list of {name}:".format(name=self.name) + " ".join([str(i) for i in self.reports])

    @classmethod
    @cache.memoize(timeout=60*60*12)
    def generate_marks(cls, group: Group, course: int) -> list:
        course = Course.query.get(course)
        marks_lst = []
        for i in group.students:
            reports = Report.query.filter_by(report_course=course.course_id,
                                             report_student=i.id).order_by(Report.report_num)
            marks_lst.append(cls(i, reports, course.labs_amount))
        return marks_lst

    @staticmethod
    @celery.task(ignore_result=True)
    def drop_marks_cache(report_id):
        with app.app_context():
            report = Report.query.get(report_id)
            course = Course.query.get(report.report_course)
            group = User.query.get(report.report_student).group[0]
            cache.delete_memoized(ReportsProcessor.generate_marks, ReportsProcessor, group, course.course_id)

    @staticmethod
    def user_has_course(user: int, course: int) -> bool:
        group = User.query.get(user).group[0]
        courses_of_stu = [i.course_id for i in group.courses]
        return course in courses_of_stu


class GroupStats(View):
    decorators = [login_required]

    def dispatch_request(self, *args, **kwargs):
        if not ReportsProcessor.user_has_course(current_user.id, kwargs.get('course')):
            abort(404)
        return render_template('student/group_stats.html',
                               marks=ReportsProcessor.generate_marks(current_user.group[0],
                                                                     kwargs.get('course')))

