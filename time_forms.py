import datetime
import math
import time

from django.forms import widgets as django_widgets
from django import forms as django_forms

TIME_FORMAT = "%I:%M %p"

def to_24_hr(hour, am_pm):
    hour = int(hour)
    if hour <= 12 and hour >= 1:
        if am_pm == 'am':
            if hour == 12:
                return 0
            else:
                return hour
        elif am_pm == 'pm':
            if hour == 12:
                return 12
            else:
                return hour + 12
    return None

def to_12_hr(hour):
    hour = int(hour)

    if hour == 0:
        return 12
    elif hour > 12 and hour < 24:
        return hour - 12
    else:
        return hour

def get_ampm(value):
    def int_ampm(int_value):
        try:
            int_value = int(int_value)
        except Exception:
            return None

        if int_value >= 12 and int_value < 24:
            return 'PM'
        else:
            return 'AM'

    if isinstance(value, (datetime.datetime, datetime.time,)):
        return value.strftime('%p')
    elif isinstance(value, (unicode, str, int,)):
        return int_ampm(value)
    else:
        return None

def round_to_five_minutes(actual_minute):
    return int(math.ceil(int(actual_minute)/5)*5)

class TimeOptionChoices(object):

    BLANK_CHOICE = ('', '---',)

    @classmethod
    def hours(cls):
        hours = [(x, x,) for x in xrange(1,13)]
        hours.insert(0, cls.BLANK_CHOICE)
        return hours

    @classmethod
    def minutes(cls):
        minutes = [(x,'0' + str(x)) for x in xrange(0, 10, 5)]
        minutes.extend([(x, x,) for x in xrange(10, 60, 5)])
        minutes.insert(0, cls.BLANK_CHOICE)
        return minutes

    @classmethod
    def ampm(cls):
        ampm = (cls.BLANK_CHOICE, ('am', 'AM',), ('pm', 'PM',),)
        return ampm

class HourSelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'hours-select'}):
        super(HourSelectWidget, self).__init__(attrs)
        self.choices = TimeOptionChoices.hours()

class MinuteSelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'minutes-select'}):
        super(MinuteSelectWidget, self).__init__(attrs)
        self.choices = TimeOptionChoices.minutes()

class AmPmSelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'ampm-select'}):
        super(AmPmSelectWidget, self).__init__(attrs)
        self.choices = TimeOptionChoices.ampm()

class SplitTimeSelectWidget(django_widgets.MultiWidget):

    def __init__(self, attrs=None):
        widgets = []
        widgets.append(HourSelectWidget())
        widgets.append(MinuteSelectWidget())
        widgets.append(AmPmSelectWidget())
        widgets = tuple(widgets)

        super(SplitTimeSelectWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        # value arg in should be field's cleaned value

        if not value:
            return [None, None, None]

        if value:
            hour = to_12_hr(value.hour)
            min = round_to_five_minutes(value.minute)
            am_or_pm = get_ampm(value.hour).lower()

            return [hour, min, am_or_pm,]

class SplitTimeField(django_forms.MultiValueField):

    FIELD_NAMES = ('hours', 'minutes', 'ampm',)
    widget = SplitTimeSelectWidget

    def __init__(self, *args, **kwargs):

        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(TimeOptionChoices, field_name)
            choice_field = django_forms.ChoiceField(choices=choice())
            fields.append(choice_field)
        fields = tuple(fields)

        super(SplitTimeField, self).__init__(
            fields, *args, **kwargs)

    def compress(self, data_list):

        if not data_list:
            return None

        if data_list:
            hour = data_list[0]
            min = data_list[1]
            am_or_pm = data_list[2]

            s = time.strptime('{0}:{1} {2}'.format(
                hour, min, am_or_pm),
                TIME_FORMAT)
            # convert to datetime.time
            s = datetime.datetime(*s[:6]).time()
            return s

if __name__ == '__main__':
    import os, sys
    sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'tests',
        'django_more_forms_tests',))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_more_forms_tests.settings'

    import unittest
    from django.test import SimpleTestCase

    class TestGetAmPm(SimpleTestCase):
        def test_get_with_int(self):
            self.assertEqual(get_ampm(1), 'AM')
            self.assertEqual(get_ampm(5), 'AM')
            self.assertEqual(get_ampm(12), 'PM')
            self.assertEqual(get_ampm(20), 'PM')

        def test_get_with_time(self):
            self.assertEqual(get_ampm(datetime.time(hour=1)), 'AM')
            self.assertEqual(get_ampm(datetime.time(hour=5)), 'AM')
            self.assertEqual(get_ampm(datetime.time(hour=12)), 'PM')
            self.assertEqual(get_ampm(datetime.time(hour=20)), 'PM')

        def test_get_with_datetime(self):
            def create_dt(hour):
                return datetime.datetime(year=2000, month=1, day=1,
                    hour=hour)
            self.assertEqual(get_ampm(create_dt(1)), 'AM')
            self.assertEqual(get_ampm(create_dt(5)), 'AM')
            self.assertEqual(get_ampm(create_dt(12)), 'PM')
            self.assertEqual(get_ampm(create_dt(20)), 'PM')

        def test_get_with_string(self):
            self.assertEqual(get_ampm('1'), 'AM')
            self.assertEqual(get_ampm('5'), 'AM')
            self.assertEqual(get_ampm('12'), 'PM')
            self.assertEqual(get_ampm('20'), 'PM')

    class TimeOptionChoicesTest(SimpleTestCase):

        def setUp(self):
            self.hours = TimeOptionChoices.hours()
            self.minutes = TimeOptionChoices.minutes()
            self.ampm = TimeOptionChoices.ampm()

        def test_hours_choices_exist(self):
            # plus one for blank
            self.assertEqual(len(self.hours), 12 + 1)

        def test_minutes_choices_exist(self):
            self.assertEqual(len(self.minutes), 60/5 + 1)

        def test_ampm_choices_exist(self):
            self.assertEqual(len(self.ampm), 2 + 1)

        def test_blanks(self):
            self.assertIn('---', map(lambda x: x[1], self.hours))
            self.assertIn('---', map(lambda x: x[1], self.minutes))
            self.assertIn('---', map(lambda x: x[1], self.ampm))

    class TimeSelectWidgets(SimpleTestCase):

        def setUp(self):
            w = HourSelectWidget()
            self.rendered_hours = w.render('hours', '')
            w = MinuteSelectWidget()
            self.rendered_minutes = w.render('minutes', '')
            w = AmPmSelectWidget()
            self.rendered_ampm = w.render('ampm', '')

        def test_hour_widget(self):
            w_rendered_expect = '<select class="hours-select" name="hours">'
            self.assertIn(w_rendered_expect, self.rendered_hours)

            self.assertIn('<option ', self.rendered_hours)
            for value, display_value in TimeOptionChoices.hours():
                self.assertIn(unicode(value), self.rendered_hours)
                self.assertIn(unicode(display_value), self.rendered_hours)

        def test_minute_widget(self):
            w_rendered_expect = \
                '<select class="minutes-select" name="minutes">'
            self.assertIn(w_rendered_expect, self.rendered_minutes)

            self.assertIn('<option ', self.rendered_minutes)
            for value, display_value in TimeOptionChoices.minutes():
                self.assertIn(unicode(value), self.rendered_minutes)
                self.assertIn(unicode(display_value), self.rendered_minutes)

        def test_ampm_widget(self):
            w_rendered_expect = '<select class="ampm-select" name="ampm">'
            self.assertIn(w_rendered_expect, self.rendered_ampm)

            self.assertIn('<option ', self.rendered_ampm)
            for value, display_value in TimeOptionChoices.ampm():
                self.assertIn(unicode(value), self.rendered_ampm)
                self.assertIn(unicode(display_value), self.rendered_ampm)

    class SplitTimeSelectWidgetTest(SimpleTestCase):

        def setUp(self):
            self.w = SplitTimeSelectWidget()
            self.rendered = self.w.render('time-select', '')

        def test_widget_rendering_all_widgets(self):
            # tests render
            self.assertIn('<select class="hours-select" name="time-select_0"', self.rendered)
            self.assertIn('<select class="minutes-select" name="time-select_1', self.rendered)
            self.assertIn('<select class="ampm-select" name="time-select_2', self.rendered)

        def test_widget_with_value(self):
            for hr_value, hr_display in TimeOptionChoices.hours():
                for min_value, min_display in TimeOptionChoices.minutes():
                    for ampm_value, ampm_display in TimeOptionChoices.ampm():
                        if hr_value and min_value and ampm_value:
                            # tests decompress
                            exact_time = datetime.time(
                                hour=to_24_hr(hr_value, ampm_value),
                                minute=min_value)
                            self.rendered = self.w.render('time-select',
                                exact_time)
                            hour_assert = '<option value="{0}" selected="selected">{1}'.format(hr_value, hr_display)
                            minute_assert = '<option value="{0}" selected="selected">{1}'.format(min_value, min_display)
                            ampm_assert = '<option value="{0}" selected="selected">{1}'.format(ampm_value, ampm_display)
                            self.assertIn(hour_assert, self.rendered)
                            self.assertIn(minute_assert, self.rendered)
                            self.assertIn(ampm_assert, self.rendered)

    class SplitTimeFieldTest(SimpleTestCase):

        def test_create(self):
            field = SplitTimeField()
            self.assertTrue(field)

        def test_clean_pass(self):
            field = SplitTimeField()
            value = field.clean(['1', '5', 'am'])
            self.assertEqual(value, datetime.time(1, 5))
            value = field.clean(['5', '5', 'am'])
            self.assertEqual(value, datetime.time(5, 5))
            value = field.clean(['12', '5', 'pm'])
            self.assertEqual(value, datetime.time(12, 5))
            value = field.clean(['8', '5', 'pm'])
            self.assertEqual(value, datetime.time(20, 5))

        def test_initial_current_time(self):
            current_time = datetime.datetime.now().time()
            field = SplitTimeField()
            html_output = str(field.widget.render('testing', current_time))
            hour_assert = '<option value="{0}" selected="selected">'.format(to_12_hr(current_time.hour))
            minute_assert = '<option value="{0}" selected="selected">'.format(round_to_five_minutes(current_time.minute))
            ampm_assert = '<option value="{0}" selected="selected">'.format(get_ampm(current_time.hour).lower())
            self.assertIn(hour_assert, html_output)
            self.assertIn(minute_assert, html_output)
            self.assertIn(ampm_assert, html_output)

    class TimeConversion(SimpleTestCase):

        def test_to_24_input_is_twelve_pass(self):
            valid = {
                'am': dict([(i, i,) for i in range(1, 12)] + [(12, 0)]),
                'pm': dict([(1, 13,), (2, 14,), (3, 15,), (4, 16,),
                    (5, 17,), (6, 18,), (7, 19,), (8, 20,), (9, 21,),
                    (10, 22,), (11, 23,), (12, 12,)])}
            for am_pm in ['am', 'pm',]:
                for v in range(1, 12):
                    self.assertEqual(to_24_hr(v, am_pm), valid[am_pm][v])

        def test_to_12_input_is_twenty_four_pass(self):
            valid = [
                (23, 11,), (22, 10,), (21, 9,), (20, 8,),
                (19, 7,), (18, 6,), (17, 5,), (16, 4,),
                (15, 3,), (14, 2,), (13, 1,), (12, 12,),
                (11, 11,), (10, 10,), (9, 9,), (8, 8,),
                (7, 7,), (6, 6,), (5, 5,), (4, 4,),
                (3, 3,), (2, 2,), (1, 1,),]
            for twenty_four, twelve in valid:
                converted_twelve = to_12_hr(twenty_four)
                self.assertEqual(twelve, converted_twelve)

    unittest.main()
