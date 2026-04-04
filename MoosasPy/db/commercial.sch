! Commercial Building (Mall/Retail) Schedule
! Based on: GB50189-2015 Appendix D (Table D.0.9-6 商场建筑)
! OccupantDensity unit: person/m²
! OccupantHeatGain unit: W/person (light walking/shopping activity)
! EquipmentHeatGain unit: W/m²
! LightingHeatGain unit: W/m²
!
COM_OccDens_Weekday,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.05,0.125,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.2,0.175,0.125,0.0,0.0
COM_OccDens_Weekend,Daily,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.05,0.15,0.225,0.2375,0.2375,0.2375,0.225,0.225,0.225,0.225,0.225,0.2125,0.175,0.125,0.0,0.0
COM_OccHeat_AllDay,Daily,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0,100.0
COM_EquipHeat_Weekday,Daily,3.9,3.9,3.9,3.9,3.9,3.9,3.9,5.2,7.8,10.4,11.7,11.7,11.7,11.7,11.7,11.7,11.7,11.7,11.7,11.7,11.05,9.1,6.5,4.55
COM_EquipHeat_Weekend,Daily,3.9,3.9,3.9,3.9,3.9,3.9,3.9,5.2,7.8,11.05,12.35,12.35,12.35,12.35,12.35,12.35,12.35,12.35,12.35,11.7,11.05,9.1,6.5,4.55
COM_LightHeat_Weekday,Daily,0.9,0.9,0.9,0.9,0.9,0.9,0.9,1.8,4.5,8.1,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,8.1,6.3,2.7,0.9
COM_LightHeat_Weekend,Daily,0.9,0.9,0.9,0.9,0.9,0.9,0.9,1.8,4.5,8.55,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,9.0,8.1,6.3,2.7,0.9
!
OccupantDensity,Weekly,COM_OccDens_Weekday,COM_OccDens_Weekday,COM_OccDens_Weekday,COM_OccDens_Weekday,COM_OccDens_Weekday,COM_OccDens_Weekend,COM_OccDens_Weekend
OccupantHeatGain,Weekly,COM_OccHeat_AllDay,COM_OccHeat_AllDay,COM_OccHeat_AllDay,COM_OccHeat_AllDay,COM_OccHeat_AllDay,COM_OccHeat_AllDay,COM_OccHeat_AllDay
EquipmentHeatGain,Weekly,COM_EquipHeat_Weekday,COM_EquipHeat_Weekday,COM_EquipHeat_Weekday,COM_EquipHeat_Weekday,COM_EquipHeat_Weekday,COM_EquipHeat_Weekend,COM_EquipHeat_Weekend
LightingHeatGain,Weekly,COM_LightHeat_Weekday,COM_LightHeat_Weekday,COM_LightHeat_Weekday,COM_LightHeat_Weekday,COM_LightHeat_Weekday,COM_LightHeat_Weekend,COM_LightHeat_Weekend
