! Hotel Building Schedule
! Conservative profile for guest rooms and public areas
! OccupantDensity unit: person/m虏
! OccupantHeatGain unit: W/person
! EquipmentHeatGain unit: W/m虏
! LightingHeatGain unit: W/m虏
!
HOT_OccDens_Weekday,Daily,0.01,0.01,0.01,0.01,0.01,0.02,0.04,0.06,0.08,0.10,0.12,0.12,0.12,0.12,0.12,0.10,0.08,0.06,0.05,0.04,0.03,0.02,0.015,0.01
HOT_OccDens_Weekend,Daily,0.02,0.02,0.02,0.02,0.02,0.03,0.05,0.08,0.10,0.12,0.14,0.16,0.16,0.16,0.16,0.14,0.12,0.10,0.08,0.06,0.05,0.04,0.03,0.02
HOT_OccHeat_AllDay,Daily,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0,70.0
HOT_EquipHeat_Weekday,Daily,0.5,0.5,0.5,0.5,0.5,0.8,1.2,1.6,2.0,2.4,2.8,2.8,2.8,2.8,2.8,2.4,2.0,1.6,1.2,1.0,0.8,0.7,0.6,0.5
HOT_EquipHeat_Weekend,Daily,0.6,0.6,0.6,0.6,0.6,0.8,1.0,1.2,1.4,1.6,1.8,1.8,1.8,1.8,1.8,1.6,1.4,1.2,1.0,0.9,0.8,0.7,0.6,0.6
HOT_LightHeat_Weekday,Daily,0.1,0.1,0.1,0.1,0.1,0.2,0.4,0.6,0.8,1.0,1.2,1.2,1.2,1.2,1.2,1.0,0.8,0.6,0.4,0.3,0.2,0.2,0.1,0.1
HOT_LightHeat_Weekend,Daily,0.2,0.2,0.2,0.2,0.2,0.2,0.3,0.4,0.5,0.6,0.8,0.8,0.8,0.8,0.8,0.6,0.5,0.4,0.3,0.3,0.2,0.2,0.2,0.2
!
HOT_OccDens_Weekly,Weekly,HOT_OccDens_Weekday,HOT_OccDens_Weekday,HOT_OccDens_Weekday,HOT_OccDens_Weekday,HOT_OccDens_Weekday,HOT_OccDens_Weekend,HOT_OccDens_Weekend
HOT_OccHeat_Weekly,Weekly,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay,HOT_OccHeat_AllDay
HOT_EquipHeat_Weekly,Weekly,HOT_EquipHeat_Weekday,HOT_EquipHeat_Weekday,HOT_EquipHeat_Weekday,HOT_EquipHeat_Weekday,HOT_EquipHeat_Weekday,HOT_EquipHeat_Weekend,HOT_EquipHeat_Weekend
HOT_LightHeat_Weekly,Weekly,HOT_LightHeat_Weekday,HOT_LightHeat_Weekday,HOT_LightHeat_Weekday,HOT_LightHeat_Weekday,HOT_LightHeat_Weekday,HOT_LightHeat_Weekend,HOT_LightHeat_Weekend
