! Residential Building Schedule
! Based on: JGJ26-2018, JGJ134-2010, GB50189-2015 Appendix D
! OccupantDensity unit: person/m²
! OccupantHeatGain unit: W/person (sensible heat, light activity)
! EquipmentHeatGain unit: W/m²
! LightingHeatGain unit: W/m²
!
! Weekday schedule: residents mostly at home in morning and evening
! Weekend schedule: residents at home most of the day
!
RES_OccDens_Weekday,Daily,0.0281,0.0281,0.0281,0.0281,0.0281,0.0264,0.0231,0.0165,0.0066,0.0066,0.0066,0.0066,0.0066,0.0066,0.0066,0.0066,0.0099,0.0198,0.0264,0.0281,0.0281,0.0281,0.0281,0.0281
RES_OccDens_Weekend,Daily,0.0281,0.0281,0.0281,0.0281,0.0281,0.0281,0.0264,0.0248,0.0231,0.0215,0.0215,0.0215,0.0215,0.0215,0.0215,0.0215,0.0215,0.0231,0.0248,0.0264,0.0281,0.0281,0.0281,0.0281
RES_OccHeat_AllDay,Daily,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0
RES_EquipHeat_Weekday,Daily,0.86,0.64,0.64,0.64,0.64,1.07,2.15,2.58,1.29,0.86,0.86,0.86,1.29,0.86,0.86,0.86,1.29,2.15,3.01,3.44,3.01,2.15,1.29,0.86
RES_EquipHeat_Weekend,Daily,0.86,0.64,0.64,0.64,0.64,0.86,1.72,2.58,3.01,2.79,2.58,2.58,3.01,2.58,2.37,2.37,2.58,2.79,3.22,3.44,3.01,2.37,1.5,0.86
RES_LightHeat_Weekday,Daily,0.25,0.25,0.25,0.25,0.25,0.5,1.5,1.0,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.25,0.5,1.5,3.0,4.0,3.5,2.5,1.0,0.5
RES_LightHeat_Weekend,Daily,0.25,0.25,0.25,0.25,0.25,0.25,0.75,1.5,2.0,1.75,1.5,1.25,1.25,1.25,1.25,1.25,1.5,2.0,3.0,4.0,3.5,2.75,1.5,0.5
!
RES_OccDens_Weekly,Weekly,RES_OccDens_Weekday,RES_OccDens_Weekday,RES_OccDens_Weekday,RES_OccDens_Weekday,RES_OccDens_Weekday,RES_OccDens_Weekend,RES_OccDens_Weekend
RES_OccHeat_Weekly,Weekly,RES_OccHeat_AllDay,RES_OccHeat_AllDay,RES_OccHeat_AllDay,RES_OccHeat_AllDay,RES_OccHeat_AllDay,RES_OccHeat_AllDay,RES_OccHeat_AllDay
RES_EquipHeat_Weekly,Weekly,RES_EquipHeat_Weekday,RES_EquipHeat_Weekday,RES_EquipHeat_Weekday,RES_EquipHeat_Weekday,RES_EquipHeat_Weekday,RES_EquipHeat_Weekend,RES_EquipHeat_Weekend
RES_LightHeat_Weekly,Weekly,RES_LightHeat_Weekday,RES_LightHeat_Weekday,RES_LightHeat_Weekday,RES_LightHeat_Weekday,RES_LightHeat_Weekday,RES_LightHeat_Weekend,RES_LightHeat_Weekend
