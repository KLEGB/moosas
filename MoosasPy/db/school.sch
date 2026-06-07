! School Building Schedule
! Based on: GB50189-2015 Appendix D (Table D.0.9-6 教学楼)
! OccupantDensity unit: person/m²
! OccupantHeatGain unit: W/person (sedentary classroom activity)
! EquipmentHeatGain unit: W/m²
! LightingHeatGain unit: W/m²
!
SCH_OccDens_Weekday,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0167,0.0835,0.1587,0.1587,0.1587,0.1336,0.1336,0.1587,0.1587,0.1587,0.0501,0.0167,0.0,0.0,0.0,0.0,0.0
SCH_OccDens_Weekend,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
SCH_OccHeat_AllDay,Daily,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0
SCH_EquipHeat_Weekday,Daily,0.5,0.5,0.5,0.5,0.5,0.5,0.5,1.0,2.0,4.0,4.0,4.0,3.0,3.0,4.0,4.0,4.0,1.5,0.75,0.5,0.5,0.5,0.5,0.5
SCH_EquipHeat_Weekend,Daily,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25
SCH_LightHeat_Weekday,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.8,4.0,8.0,8.0,8.0,6.4,6.4,8.0,8.0,8.0,2.4,0.8,0.0,0.0,0.0,0.0,0.0
SCH_LightHeat_Weekend,Daily,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4,0.4
!
SCH_OccDens_Weekly,Weekly,SCH_OccDens_Weekday,SCH_OccDens_Weekday,SCH_OccDens_Weekday,SCH_OccDens_Weekday,SCH_OccDens_Weekday,SCH_OccDens_Weekend,SCH_OccDens_Weekend
SCH_OccHeat_Weekly,Weekly,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay,SCH_OccHeat_AllDay
SCH_EquipHeat_Weekly,Weekly,SCH_EquipHeat_Weekday,SCH_EquipHeat_Weekday,SCH_EquipHeat_Weekday,SCH_EquipHeat_Weekday,SCH_EquipHeat_Weekday,SCH_EquipHeat_Weekend,SCH_EquipHeat_Weekend
SCH_LightHeat_Weekly,Weekly,SCH_LightHeat_Weekday,SCH_LightHeat_Weekday,SCH_LightHeat_Weekday,SCH_LightHeat_Weekday,SCH_LightHeat_Weekday,SCH_LightHeat_Weekend,SCH_LightHeat_Weekend
