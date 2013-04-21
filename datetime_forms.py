import math
import datetime
import itertools

import pytz
from django.utils import timezone
from django import forms
from django.utils.safestring import mark_safe

class CalendarOptionValues(object):

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
        years = [(x, x,) for x in xrange(timezone.now().year-1, timezone.now().year+1)]
        years.insert(0, cls.BLANK_CHOICE)
        return years

class TimeOptionValues(object):

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

class DateTimeOptionValues(CalendarOptionValues, TimeOptionValues):
    pass

# widgets

class SplitDateSelectWidget(forms.MultiWidget):
    FIELD_NAMES = ('months', 'days', 'years',)

    def __init__(self, attrs=None):
        widgets = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(CalendarOptionValues, field_name)
            select_option = forms.Select(choices=choice(),
                attrs={'class': field_name + '-select'})
            widgets.append(select_option)
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

class SplitTimeSelectWidget(forms.MultiWidget):
    FIELD_NAMES = ('hours', 'minutes', 'ampm',)

    def __init__(self, attrs=None):
        widgets = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(TimeOptionValues, field_name)
            select_option = forms.Select(choices=choice(),
                attrs={'class': field_name + '-select'})
            widgets.append(select_option)
        widgets = tuple(widgets)

        super(SplitTimeSelectWidget, self).__init__(
            widgets, attrs)

    def _get_five_minute(self, actual_minute):
        return int(math.ceil(int(actual_minute)/5)*5)

    def decompress(self, value):
        if value:
            if not timezone.is_aware(value):
                value = datetime.datetime(
                    month=4, day=22, year=2000,
                    hour=value.hour,
                    minute=value.minute,
                    second=value.second,
                    tzinfo=pytz.utc)
            value = timezone.localtime(value)
            return [
                int(value.strftime("%I")),
                self._get_five_minute(value.strftime("%M")),
                value.strftime("%p").lower()]
        return [None, None, None]

# fields

class SplitDateSelectField(forms.MultiValueField):
    FIELD_NAMES = ('months', 'days', 'years',)
    widget = SplitDateSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(CalendarOptionValues, field_name)
            fields.append(forms.ChoiceField(choices=choice()))
        fields = tuple(fields)

        super(SplitDateSelectField, self).__init__(
            fields, *args, **kwargs)

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

class SplitTimeSelectField(forms.MultiValueField):
    FIELD_NAMES = ('hours', 'minutes', 'ampm',)
    widget = SplitTimeSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(TimeOptionValues, field_name)
            choice_field = forms.ChoiceField(choices=choice())
            fields.append(choice_field)
        fields = tuple(fields)

        super(SplitTimeSelectField, self).__init__(
            fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            to_dt = '4/22/2000 %s:%s %s' % (
                data_list[0],
                data_list[1],
                data_list[2],)
            result = timezone.make_aware(
                datetime.datetime.strptime(to_dt, '%m/%d/%Y %I:%M %p'),
                timezone.get_current_timezone())
            return result
        return None

class SplitDateTimeSelectWidget(forms.MultiWidget):

    def __init__(self, attrs=None):
        widgets = []
        for field_name in itertools.chain(SplitDateSelectWidget.FIELD_NAMES, SplitTimeSelectWidget.FIELD_NAMES):
            if field_name in SplitDateSelectWidget.FIELD_NAMES:
                class_name = CalendarOptionValues
            elif field_name in SplitTimeSelectWidget.FIELD_NAMES:
                class_name = TimeOptionValues
            else:
                raise Exception
            choice = getattr(class_name, field_name)
            select_option = forms.Select(choices=choice(),
                attrs={'class': field_name + '-select'})
            widgets.append(select_option)
        widgets = tuple(widgets)
        super(SplitDateTimeSelectWidget, self).__init__(
            widgets, attrs)

    def render(self, *args, **kwargs):
        r = super(SplitDateTimeSelectWidget, self).render(
            *args, **kwargs)
        r = r.replace('<select class="hours-select" id="id_timestamp_3"',
            '</div><div class="control-group"><select class="hours-select" id="id_timestamp_3"')
        return mark_safe(r)

    def _get_five_minute(self, actual_minute):
        return int(math.ceil(int(actual_minute)/5)*5)

    def decompress(self, value):
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
                self._get_five_minute(value.strftime("%M")),
                value.strftime("%p").lower()]
        return [None, None, None, None, None, None]

class SplitDateTimeSelectField(forms.MultiValueField):
    widget = SplitDateTimeSelectWidget

    def __init__(self, *args, **kwargs):
        fields = []
        for field_name in itertools.chain(SplitDateSelectField.FIELD_NAMES, SplitTimeSelectField.FIELD_NAMES):
            if field_name in SplitDateSelectField.FIELD_NAMES:
                class_name = CalendarOptionValues
            elif field_name in SplitTimeSelectField.FIELD_NAMES:
                class_name = TimeOptionValues
            else:
                raise Exception
            choice = getattr(class_name, field_name)
            choice_field = forms.ChoiceField(choices=choice())
            fields.append(choice_field)
        fields = tuple(fields)
        super(SplitDateTimeSelectField, self).__init__(
            fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            to_dt = '%s/%s/%s %s:%s %s' % (
                data_list[0],
                data_list[1],
                data_list[2],
                data_list[3],
                data_list[4],
                data_list[5],)
            result = timezone.make_aware(
                datetime.datetime.strptime(to_dt, '%m/%d/%Y %I:%M %p'),
                timezone.get_current_timezone())
            return result
        return None

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
                dt = getattr(kwargs.get('instance'), field_name)
                new_dt = dt.astimezone(timezone.get_default_timezone())
                kwargs['initial'].update({ field_name: new_dt })
            else:
                kwargs['initial'].update({ field_name: timezone.now() })
        return kwargs

    def _set_time_on(self, field_names, kwargs):
        if 'initial' not in kwargs:
            kwargs['initial'] = {}

        for field_name in field_names:
            if kwargs.get('instance', None) is not None:
                t = getattr(kwargs.get('instance'), field_name)
                kwargs['initial'].update({ field_name: t })
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

    time_amount = forms.IntegerField(required=False,
        label="",
        min_value=1)
    time_metric = forms.ChoiceField(required=False,
        label="",
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
