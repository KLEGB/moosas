from MoosasPy.transform import TransformOptions, transform
from MoosasPy.simulation.coupling.energy_radiation import run_energy_with_radiation
from MoosasPy.simulation.weather import prepare_epw

model_noshading = transform(
    "test/caseFile/DOE-facade.geo",
    options=TransformOptions(attach_shading=False),
)

model_with_shading = transform(
    "test/caseFile/DOE-facade.geo",
    options=TransformOptions(attach_shading=True),
)

prepared = prepare_epw(
    "MoosasPy/db/CHN_BJ_Beijing-Nanyuan.AP.545120_TMYx.epw",
    "temp",
)

result_with_shading = run_energy_with_radiation(
    model_with_shading,
    weather=prepared.weather,
    cumulative_skies=prepared.cumulative_skies,
    spatial_scale="zone",
)

result_noshading = run_energy_with_radiation(
    model_noshading,
    weather=prepared.weather,
    cumulative_skies=prepared.cumulative_skies,
    spatial_scale="zone",
)

print("zone, cooling_without, cooling_with, cooling_delta, heating_without, heating_with, heating_delta")
for space, without_shading, with_shading in zip(
    model_with_shading.spaceList,
    result_noshading.data["spaces"],
    result_with_shading.data["spaces"],
):
    cooling_without = float(without_shading.load["cooling"])
    cooling_with = float(with_shading.load["cooling"])
    heating_without = float(without_shading.load["heating"])
    heating_with = float(with_shading.load["heating"])
    print(
        f"{space.id}, {cooling_without:.2f}, {cooling_with:.2f}, "
        f"{cooling_with - cooling_without:+.2f}, {heating_without:.2f}, "
        f"{heating_with:.2f}, {heating_with - heating_without:+.2f}"
    )