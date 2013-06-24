import math
import datetime
import itertools

import pytz
from django.utils import timezone
from django import forms
from django.utils.safestring import mark_safe

import time_forms

class DateOptionChoices(object):

    BLANK_CHOICE = ('', '---',)

    @classmethod
    def months(cls):
        months = [(x, datetime.date(month=x,day=1,year=2010).strftime('%B'),) for x in xrange(1, 12)]
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

class MonthSelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': 'hours-select'}):
        self.choices = DateOptionChoices.months()
        super(MonthSelectWidget, self).__init__(attrs)

class DaySelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': 'minutes-select'}):
        self.choices = DateOptionChoices.days()
        super(DaySelectWidget, self).__init__(attrs)

class YearSelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': ampm-select}):
        self.choices = DateOptionChoices.years()
        super(YearSelectWidget, self).__init__(attrs)

class SplitDateSelectWidget(forms.MultiWidget):

    FIELD_NAMES = ('months', 'days', 'years',)

    def __init__(self, attrs=None):
        widgets = []
        widgets.append(MonthSelectWidget())
        widgets.append(DaySelectWidget())
        widgets.append(YearSelectWidget())
        widgets = tuple(widgets)
        super(SplitDateSelectWidget, self).__init__(
            widgets, attrs)

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

class SplitDateField(forms.MultiValueField):

    FIELD_NAMES = ('months', 'days', 'years',)
    widget = SplitDateSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(DateOptionChoices, field_name)
            fields.append(forms.ChoiceField(choices=choice()))
        fields = tuple(fields)

        super(SplitDateField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            to_dt = '%s/%s/%s' % (
                data_list[0],
                data_list[1],
                data_list[2])
            result = timezone.make_aware(
                datetime.datetime.strptime(to_dt, '%m/%d/%Y'),
                timezone.get_current_timezone())
            return result
        return None

class SplitDateTimeSelectWidget(SplitDateSelectWidget,
    time_forms.SplitTimeSelectWidget):

    def __init__(self, attrs=None):
        SplitDateSelectWidget.__init__(self, widgets, attrs)
        time_forms.SplitTimeSelectWidget.__init__(self, widgets, attrs)

    def render(self, *args, **kwargs):
        date_html = \
            SplitDateSelectWidget.render(self, *args, **kwargs)
        time_html = \
            time_forms.SplitTimeSelectWidget.__init__(self, *args,
                **kwargs)
        time_html = time_html.replace('<select class="hours-select" id="id_timestamp_3"', '</div><div class="control-group"><select class="hours-select" id="id_timestamp_3"')
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

class SplitDateTimeSelectField(forms.MultiValueField):

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

class DurationForm(forms.Form):

    time_amount = forms.IntegerField(required=False, label="", min_value=1)
    time_metric = forms.ChoiceField(required=False, label="",
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
