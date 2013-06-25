import math
import time

from django.forms import widgets as django_widgets
from django import forms as django_forms

TIME_FORMAT = "%I:%M %p"

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
            hour = value.tm_hour
            min = value.tm_min
            am_or_pm = 'am' if hour < 12 else 'pm'

            return [hour, round_to_five_minutes(min), am_or_pm,]

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
            return s
