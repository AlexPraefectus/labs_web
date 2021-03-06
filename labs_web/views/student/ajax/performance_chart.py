from flask.views import View
from flask_login import login_required, current_user
from labs_web.extensions import User, db, Report, cache, Course, Group
from flask import jsonify, abort
from statistics import mean, StatisticsError
from random import randint, choice
import datetime


@cache.memoize(24 * 60 * 60)
def performance_of_lab_group(lab_number: int, group_id: int, course_id: int) -> float:
    marks_of_group = [report.report_mark for report in Report.query.filter(
        Report.report_num == lab_number,
        Report.report_student.in_([i.id for i in Group.query.get(group_id).students]),
        Report.report_course == course_id,
        Report.report_mark.isnot(None)).all()]
    try:
        return round(mean(marks_of_group), 2)
    except StatisticsError:
        return 0


@cache.memoize(24 * 24 * 60)
def performance_of_lab_course(lab_number: int, course_id: int) -> float:
    marks_of_course = [report.report_mark for report in Report.query.filter(Report.report_num == lab_number,
                                                                            Report.report_course == course_id,
                                                                            Report.report_mark.isnot(None)).all()]
    try:
        return round(mean(marks_of_course), 2)
    except StatisticsError:
        return 0


def performance_of_lab(lab_number: int, user_id: int, course_id: int):
    lab_of_student = Report.query.filter(Report.report_num == lab_number,
                                         Report.report_student == user_id,
                                         Report.report_course == course_id,
                                         Report.report_mark.isnot(None)).first()
    return [lab_number,
            lab_of_student.report_mark if lab_of_student else 0,
            performance_of_lab_group(lab_number, current_user.group[0].group_id, course_id),
            performance_of_lab_course(lab_number, course_id)]


class PerformanceChartAjax(View):
    decorators = [login_required]

    def dispatch_request(self, *args, **kwargs):
        # fill db with random test data (with no duplicated rows)
        # for course in current_user.group[0].courses:
        #     for group in course.groups:
        #         for student in group.students:
        #             lab_numbers = {randint(1, course.labs_amount) for i in range(course.labs_amount)}
        #             for i in lab_numbers:
        #                 if not Report.query.filter(Report.report_student == student.id,
        #                                            Report.report_course == course.course_id,
        #                                            Report.report_num == i).first():
        #                     report = Report(report_student=student.id,
        #                                     report_mark=randint(1, course.lab_max_score),
        #                                     report_num=i,
        #                                     report_uploaded=datetime.datetime.utcnow(),
        #                                     report_course=course.course_id,
        #                                     report_hash="fake")
        #                     db.session.add(report)
        # db.session.commit()
        course = Course.query.get(kwargs.get('course_id'))
        if course.course_id not in [i.course_id for i in current_user.group[0].courses]:
            abort(403)
        return jsonify(
            {'name': course.course_name,
             'labs': course.labs_amount,
             'shortened': course.course_shortened,
             'data': ([performance_of_lab(i, current_user.id, course.course_id)
                       for i in range(1, course.labs_amount + 1)])
             })
