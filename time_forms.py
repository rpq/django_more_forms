import math
import time

from django import forms

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

class HourSelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': 'hours-select'}):
        self.choices = TimeOptionChoices.hours()
        super(HourSelectWidget, self).__init__(attrs)

class MinuteSelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': 'minutes-select'}):
        self.choices = TimeOptionChoices.minutes()
        super(MinuteSelectWidget, self).__init__(attrs)

class AmPmSelectWidget(forms.SelectWidget):

    def __init__(self, attrs={'class': ampm-select}):
        self.choices = TimeOptionChoices.ampm()
        super(AmPmSelectWidget, self).__init__(attrs)

class SplitTimeSelectWidget(forms.MultiWidget):

    FIELD_NAMES = ('hours', 'minutes', 'ampm',)

    def __init__(self, attrs=None):
        widgets = []
        widgets.append(HourSelectWidget())
        widgets.append(MinuteSelectWidget())
        widgets.append(AmPmSelectWidget())
        widgets = tuple(widgets)

        super(SplitTimeSelectWidget, self).__init__(
            widgets, attrs)

    def decompress(self, value):
        # value arg in should be field's cleaned value

        if not value:
            return [None, None, None]

        if value:
            hour = value.tm_hour
            min = value.tm_min
            am_or_pm = 'am' if hour < 12 else 'pm'

            return [hour, round_to_five_minutes(min), am_or_pm,]

class SplitTimeField(forms.MultiValueField):

    FIELD_NAMES = ('hours', 'minutes', 'ampm',)
    widget = SplitTimeSelectWidget

    def __init__(self, *args, **kwargs):

        fields = []
        for field_name in self.FIELD_NAMES:
            choice = getattr(TimeOptionChoices, field_name)
            choice_field = forms.ChoiceField(choices=choice())
            fields.append(choice_field)
        fields = tuple(fields)

        super(SplitTimeSelectField, self).__init__(
            fields, *args, **kwargs)

    def compress(self, data_list):

        if not data_list:
            return None

        if data_list:
            hour = data_list[0]
            min = data_list[1]
            am_or_pm = data_list[2]

            s = time.strptime('{0}:{1} {2}'.format(hour, min, am_or_pm),
                TIME_FORMAT)
            return s
