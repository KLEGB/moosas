from .settings import MoosasSettings
from ..utils import generate_code


class schType:
    Temperature = "Temperature"  # for setPoint
    AnyNumber = "Any Number"  # for on/off
    Fraction = "Fraction"  # for occ
    ControlType = "Control Type"
    OnOff = "On/Off"


class schDesignDay:
    Weekends = "Weekends"
    Weekdays = "Weekdays"
    SummerDesignDay = "SummerDesignDay"
    WinterDesignDay = "WinterDesignDay"
    Holidays = "Holidays"
    AllOtherDays = "AllOtherDays"
    AllDays = "AllDays"


CompactDefault = {
    "key": "Schedule:Compact",
    'Name': "",
    'Schedule_Type_Limits_Name': schType.AnyNumber,  # Temperature
}
TypeLimitsDefault = {
    "key": "ScheduleTypeLimits",
    'Name': "",
    'Lower_Limit_Value': '',
    'Upper_Limit_Value': '',
    'Numeric_Type': ''
}
typeLimitSettings = [
    MoosasSettings(TypeLimitsDefault, **{"Name": "Any Number"}),
    MoosasSettings(TypeLimitsDefault, **{"Name": "Fraction", "Lower_Limit_Value": 0.0, "Upper_Limit_Value": 1.0,
                                         "Numeric_Type": "CONTINUOUS"}),
    MoosasSettings(TypeLimitsDefault, **{"Name": "Temperature", "Lower_Limit_Value": -60, "Upper_Limit_Value": 200,
                                         "Numeric_Type": "CONTINUOUS"}),
    MoosasSettings(TypeLimitsDefault, **{"Name": "Control Type", "Lower_Limit_Value": 0, "Upper_Limit_Value": 4,
                                         "Numeric_Type": "DISCRETE"}),
    MoosasSettings(TypeLimitsDefault,
                   **{"Name": "On/Off", "Lower_Limit_Value": 0, "Upper_Limit_Value": 1, "Numeric_Type": "DISCRETE"}),
]


def dailySchedule(sch: dict, _type=schType.AnyNumber, _name=None):
    """schedule for any type pf design days
    sch:{schDesignDay.anything:[]*24}
    _type:schType.anything
    start from 1 AM (12:00PM ~ 1AM)
    """
    schedule = MoosasSettings(CompactDefault)
    if not _name:
        _name = 'sch_' + generate_code(4)
    kwargs = {
        'Name': _name,
        'Schedule_Type_Limits_Name': _type,
        'Field_1': 'Through: 12/31',
    }
    if len(sch) == 1:
        if list(sch.keys())[0] != schDesignDay.AllDays:
            raise TypeError(f"single sch design day must be AllDays, got {list(sch.keys())[0]}")
    elif schDesignDay.AllOtherDays not in sch.keys():
        raise TypeError(f"multi sch design days must include AllOtherDays, got {sch.keys()}")
    fieldNum = 2
    for key in sch.keys():
        kwargs[f'Field_{fieldNum}'] = f"For: {key}"
        fieldNum += 1
        if len(sch[key]) != 24:
            raise TypeError(f'daily schedule {key} must have 24 numbers, got {len(sch[key])}')
        for i in range(1, len(sch[key])):
            if sch[key][i - 1] != sch[key][i]:
                kwargs[f'Field_{fieldNum}'] = f"Until: {str(i).zfill(2)}:00, {sch[key][i - 1]}"
                fieldNum += 1
        kwargs[f'Field_{fieldNum}'] = f"Until: 24:00, {sch[key][-1]}"
        fieldNum += 1
    schedule.updateParams(**kwargs)
    return schedule
