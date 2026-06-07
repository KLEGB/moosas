! Office Building Schedule
! Based on: GB50189-2015 Appendix D (Tables D.0.9-5,6,9,3)
! OccupantDensity unit: person/m²
! OccupantHeatGain unit: W/person (sedentary office work)
! EquipmentHeatGain unit: W/m²
! LightingHeatGain unit: W/m²
!
OFF_OccDens_Weekday,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.01,0.05,0.095,0.095,0.095,0.08,0.08,0.095,0.095,0.095,0.05,0.03,0.01,0.0,0.0,0.0,0.0
OFF_OccDens_Weekend,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.005,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
OFF_OccHeat_AllDay,Daily,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0,75.0
OFF_EquipHeat_Weekday,Daily,3.0,3.0,3.0,3.0,3.0,3.0,3.0,4.5,7.5,13.5,13.5,13.5,10.5,10.5,13.5,13.5,13.5,9.0,6.0,4.5,3.0,3.0,3.0,3.0
OFF_EquipHeat_Weekend,Daily,1.5,1.5,1.5,1.5,1.5,1.5,1.5,2.25,2.25,2.25,2.25,2.25,2.25,2.25,2.25,2.25,1.5,1.5,1.5,1.5,1.5,1.5,1.5,1.5
OFF_LightHeat_Weekday,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.8,4.0,8.0,8.0,8.0,6.4,6.4,8.0,8.0,8.0,4.0,1.6,0.8,0.0,0.0,0.0,0.0
OFF_LightHeat_Weekend,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0
!
OFF_OccDens_Weekly,Weekly,OFF_OccDens_Weekday,OFF_OccDens_Weekday,OFF_OccDens_Weekday,OFF_OccDens_Weekday,OFF_OccDens_Weekday,OFF_OccDens_Weekend,OFF_OccDens_Weekend
OFF_OccHeat_Weekly,Weekly,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay,OFF_OccHeat_AllDay
OFF_EquipHeat_Weekly,Weekly,OFF_EquipHeat_Weekday,OFF_EquipHeat_Weekday,OFF_EquipHeat_Weekday,OFF_EquipHeat_Weekday,OFF_EquipHeat_Weekday,OFF_EquipHeat_Weekend,OFF_EquipHeat_Weekend
OFF_LightHeat_Weekly,Weekly,OFF_LightHeat_Weekday,OFF_LightHeat_Weekday,OFF_LightHeat_Weekday,OFF_LightHeat_Weekday,OFF_LightHeat_Weekday,OFF_LightHeat_Weekend,OFF_LightHeat_Weekend
