import math
import datetime
import itertools

import pytz
from django.utils import timezone
from django.forms import widgets as django_widgets
from django import forms as django_forms
from django.utils.safestring import mark_safe

import time_forms

class DateOptionChoices(object):

    BLANK_CHOICE = ('', '---',)

    @classmethod
    def months(cls):
        months = [(x, datetime.date(month=x,day=1,year=2010).strftime('%B'),) for x in xrange(1, 13)]
        months.insert(0, cls.BLANK_CHOICE)
        return months

    @classmethod
    def days(cls):
        days = [(x, x,) for x in xrange(1, 32)]
        days.insert(0, cls.BLANK_CHOICE)
        return days

    @classmethod
    def years(cls):
        years = [(x, x,) for x in xrange(2010, timezone.now().year+1)]
        years.insert(0, cls.BLANK_CHOICE)
        return years

class MonthSelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'months-select'}):
        super(MonthSelectWidget, self).__init__(attrs)
        self.choices = DateOptionChoices.months()

class DaySelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'days-select'}):
        super(DaySelectWidget, self).__init__(attrs)
        self.choices = DateOptionChoices.days()

class YearSelectWidget(django_widgets.Select):

    def __init__(self, attrs={'class': 'years-select' }):
        super(YearSelectWidget, self).__init__(attrs)
        self.choices = DateOptionChoices.years()

class SplitDateSelectWidget(django_widgets.MultiWidget):

    FIELD_NAMES = ('months', 'days', 'years',)

    def __init__(self, attrs=None):
        widgets = []
        widgets.append(MonthSelectWidget())
        widgets.append(DaySelectWidget())
        widgets.append(YearSelectWidget())
        widgets = tuple(widgets)
        super(SplitDateSelectWidget, self).__init__(widgets, attrs)

    def render(self, *args, **kwargs):
        r = super(SplitDateSelectWidget, self).render(
            *args, **kwargs)
        return mark_safe(r)

    def decompress(self, value):
        if value:
            value = datetime.datetime(
                month=value.month,
                day=value.day,
                year=value.year)
            return [value.month, value.day, value.year,]
        return [None, None, None,]

class SplitDateField(django_forms.MultiValueField):

    FIELD_NAMES = ('months', 'days', 'years',)
    widget = SplitDateSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(DateOptionChoices, field_name)
            fields.append(django_forms.ChoiceField(choices=choice()))
        fields = tuple(fields)

        super(SplitDateField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if not data_list:
            return None

        if data_list:
            to_dt = '%s/%s/%s' % (
                data_list[0],
                data_list[1],
                data_list[2])
            result = datetime.datetime.strptime(to_dt, '%m/%d/%Y').date()
            return result

        return None

class SplitDateTimeSelectWidget(django_widgets.MultiWidget):

    def __init__(self, attrs={'class': 'datetimeselect'}):
        #self.widgets?
        widgets = []
        self.date_widgets = SplitDateSelectWidget(
            attrs={ 'class': 'datetimeselect-date'})
        self.time_widgets = time_forms.SplitTimeSelectWidget(
            attrs={ 'class': 'datetimeselect-time' })
        widgets.extend(self.date_widgets.widgets)
        widgets.extend(self.time_widgets.widgets)
        widgets = tuple(widgets)
        super(SplitDateTimeSelectWidget, self).__init__(widgets, attrs)

    def render(self, *args, **kwargs):
        date_html = \
            self.date_widgets.render(*args, **kwargs)
        time_html = \
            self.time_widgets.render(*args, **kwargs)

        # update ids to follow date renderings
        time_html = time_html.replace('datetime_0', 'datetime_3')
        time_html = time_html.replace('datetime_1', 'datetime_4')
        time_html = time_html.replace('datetime_2', 'datetime_5')

        time_html = time_html.replace('<select class="datetimeselect-time" name="datetime_3"', '</div><div class="control-group"><select class="datetimeselect-time" name="datetime_3"')
        return mark_safe(date_html + time_html)

    def decompress(self, value):
        if not value:
            return None

        if value:
            if not timezone.is_aware(value):
                value = datetime.datetime(
                    month=value.month,
                    day=value.day,
                    year=value.year,
                    hour=value.hour,
                    minute=value.minute,
                    second=value.second,
                    tzinfo=pytz.utc)
            value = timezone.localtime(value)
            return [
                value.month,
                value.day,
                value.year,
                int(value.strftime("%I")),
                round_to_five_minutes(value.strftime("%M")),
                value.strftime("%p").lower()]

        return [None, None, None, None, None, None]

class SplitDateTimeSelectField(django_forms.MultiValueField):

    widget = SplitDateTimeSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        fields.extend(SplitDateField().fields)
        fields.extend(time_forms.SplitTimeField().fields)
        fields = tuple(fields)
        super(SplitDateTimeSelectField, self).__init__(fields, *args,
            **kwargs)

    def compress(self, data_list):
        if not data_list:
            return None

        if data_list:
            to_dt = '%s/%s/%s %s:%s %s' % (data_list[0], data_list[1],
                data_list[2], data_list[3], data_list[4], data_list[5],)
            result = timezone.make_aware(
                datetime.datetime.strptime(to_dt, '%m/%d/%Y %I:%M %p'),
                timezone.get_current_timezone())
            return result

# django datetime form helper

class TimeStampSet(object):

    def _set_ts(self, field_name, kwargs):
        current_timestamp = timezone.now()

        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        if kwargs.get('instance', None) is not None:
            kwargs['initial'].update(
                { field_name: getattr(kwargs.get('instance'), field_name) })
        else:
            kwargs['initial'].update(
                { field_name: current_timestamp })
        return kwargs

    def _set_time(self, field_name, kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        if kwargs.get('instance', None) is not None:
            kwargs['initial'].update(
                { field_name: getattr(kwargs.get('instance'), field_name) })
        else:
            kwargs['initial'].update({ field_name: timezone.now().time() })
        return kwargs

    def _set_datetime_on(self, field_names, kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        for field_name in field_names:
            if kwargs.get('instance', None) is not None:
                dt = getattr(
                    kwargs.get('instance'), field_name)
                if dt is not None:
                    new_dt = dt.astimezone(
                        timezone.get_current_timezone())
                    kwargs['initial'].update({ field_name: new_dt })
        return kwargs

    def _set_time_on(self, field_names, kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        for field_name in field_names:
            instance_ = kwargs.get('instance', None)
            if instance_ is not None:
                value = getattr(instance_, field_name)
                if not timezone.is_aware(value):
                    value = datetime.datetime(
                        month=4,
                        day=22,
                        year=2010,
                        hour=value.hour,
                        minute=value.minute,
                        second=value.second,
                        tzinfo=pytz.utc).time()
                kwargs['initial'].update({ field_name: value })
            else:
                kwargs['initial'].update(
                    { field_name: timezone.now().time() })
        return kwargs

# duration

def _get_time_metric_choices():
    TIME_METRIC_CHOICES = (
        ('min', 'Minutes',),
        ('hour', 'Hours',),)
    return TIME_METRIC_CHOICES

class DurationForm(django_forms.Form):

    time_amount = django_forms.IntegerField(required=False, label="",
        min_value=1)
    time_metric = django_forms.ChoiceField(required=False, label="",
        choices=_get_time_metric_choices())

    def clean(self):
        cleaned_data = super(DurationForm, self).clean()
        any_filled = any(cleaned_data.get(field_name, None) is not None for field_name in ('time_amount', 'time_metric',))
        all_filled = all(cleaned_data.get(field_name, None) is not None for field_name in ('time_amount', 'time_metric',))
        if any_filled and not all_filled:
            msg = 'Invalid Time Spent'
            self._errors['time_amount'] = self.error_class([msg])
            self._errors['time_metric'] = self.error_class([msg])
            del cleaned_data['time_amount']
            del cleaned_data['time_metric']
        return cleaned_data


if __name__ == '__main__':
    import os, sys
    sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'tests',
        'django_more_forms_tests',))
    os.environ['DJANGO_SETTINGS_MODULE'] = 'django_more_forms_tests.settings'

    import unittest
    from django.test import SimpleTestCase

    class DateOptionChoicesTest(SimpleTestCase):
        def setUp(self):
            self.years = DateOptionChoices.years()
            self.months = DateOptionChoices.months()
            self.days = DateOptionChoices.days()

        def test_months_choices_exist(self):
            self.assertEqual(len(self.months), 12 + 1)

        def test_days_choices_exist(self):
            self.assertEqual(len(self.days), 31 + 1)

        def test_years_choices_exist(self):
            self.assertEqual(len(self.years), 5)

        def test_blanks(self):
            self.assertIn('---', map(lambda x: x[1], self.years))
            self.assertIn('---', map(lambda x: x[1], self.months))
            self.assertIn('---', map(lambda x: x[1], self.days))

    class DateSelectWidgets(SimpleTestCase):

        def setUp(self):
            w = YearSelectWidget()
            self.rendered_years = w.render('years', '')
            w = MonthSelectWidget()
            self.rendered_months = w.render('months', '')
            w = DaySelectWidget()
            self.rendered_days = w.render('days', '')

        def test_year_widget(self):
            w_rendered_expect = '<select class="years-select" name="years">'
            self.assertIn(w_rendered_expect, self.rendered_years)

            self.assertIn('<option ', self.rendered_years)
            for value, display_value in DateOptionChoices.years():
                self.assertIn(unicode(value), self.rendered_years)
                self.assertIn(unicode(display_value), self.rendered_years)

        def test_month_widget(self):
            w_rendered_expect = \
                '<select class="months-select" name="months">'
            self.assertIn(w_rendered_expect, self.rendered_months)

            self.assertIn('<option ', self.rendered_months)
            for value, display_value in DateOptionChoices.months():
                self.assertIn(unicode(value), self.rendered_months)
                self.assertIn(unicode(display_value), self.rendered_months)

        def test_day_widget(self):
            w_rendered_expect = '<select class="days-select" name="days">'
            self.assertIn(w_rendered_expect, self.rendered_days)

            self.assertIn('<option ', self.rendered_days)
            for value, display_value in DateOptionChoices.days():
                self.assertIn(unicode(value), self.rendered_days)
                self.assertIn(unicode(display_value), self.rendered_days)

    class SplitDateSelectWidgetTest(SimpleTestCase):

        def setUp(self):
            self.w = SplitDateSelectWidget()
            self.rendered = self.w.render('date-select', '')

        def test_widget_rendering_all_widgets(self):
            # tests render
            self.assertIn('<select class="months-select" name="date-select_0"', self.rendered)
            self.assertIn('<select class="days-select" name="date-select_1', self.rendered)
            self.assertIn('<select class="years-select" name="date-select_2', self.rendered)

        def test_widget_with_value(self):
            # tests decompress
            self.rendered = self.w.render('date-select', datetime.date.today())
            month_assert = '<option value="{0}" selected="selected">'.format(
                datetime.date.today().month)
            year_assert = '<option value="{0}" selected="selected">'.format(
                datetime.date.today().year)
            day_assert = '<option value="{0}" selected="selected">'.format(
                datetime.date.today().day)

            self.assertIn(month_assert, self.rendered)
            self.assertIn(year_assert, self.rendered)
            self.assertIn(day_assert, self.rendered)

    class SplitDateFieldTest(SimpleTestCase):

        def test_date_field_create(self):
            self.date_field = SplitDateField()
            self.assertTrue(self.date_field)

        def test_date_field_clean(self):
            self.date_field = SplitDateField()
            clean_value = self.date_field.clean(
                [datetime.date.today().month,
                datetime.date.today().day,
                datetime.date.today().year])
            self.assertEqual(clean_value.__class__.__name__, 'date')
            self.assertEqual(datetime.date.today().month, clean_value.month)
            self.assertEqual(datetime.date.today().year, clean_value.year)
            self.assertEqual(datetime.date.today().day, clean_value.day)

    class SplitDateTimeWidgetTest(SimpleTestCase):

        def setUp(self):
            w = SplitDateTimeSelectWidget()
            self.rendered = w.render('datetime', '')

        def test_year_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-date" name="datetime_2">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in DateOptionChoices.years():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

        def test_month_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-date" name="datetime_0">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in DateOptionChoices.months():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

        def test_day_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-date" name="datetime_1">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in DateOptionChoices.days():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

        def test_hour_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-time" name="datetime_3">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in time_forms.TimeOptionChoices.hours():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

        def test_minute_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-time" name="datetime_4">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in time_forms.TimeOptionChoices.minutes():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

        def test_ampm_widget(self):
            w_rendered_expect = \
                '<select class="datetimeselect-time" name="datetime_5">'
            self.assertIn(w_rendered_expect, self.rendered)

            self.assertIn('<option ', self.rendered)
            for value, display_value in time_forms.TimeOptionChoices.ampm():
                self.assertIn(unicode(value), self.rendered)
                self.assertIn(unicode(display_value), self.rendered)

    class SplitDateTimeSelectFieldTest(SimpleTestCase):

        def test_create(self):
            field = SplitDateTimeSelectField()
            self.assertTrue(field)

        def test_clean_pass(self):
            field = SplitDateTimeSelectField()
            today = datetime.datetime.now()
            value = field.clean([today.month, today.day, today.year,
                today.hour,
                time_forms.round_to_five_minutes(today.minute),
                today.strftime("%p").lower()])
            self.assertEqual(value.__class__.__name__, 'datetime')

    unittest.main()
