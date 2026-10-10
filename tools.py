import requests
from langchain_core.tools import tool

# -------------------------------------------------------------
# 1. Weather Tool (يدعم الغور، المفرق، وعمّان)
# -------------------------------------------------------------
@tool
def get_live_weather(location: str):
    """Get live agricultural weather data for a location in Jordan."""

    if "مفرق" in location:
        lat, lon = 32.34, 36.21
    elif "غور" in location:
        lat, lon = 31.85, 35.50
    else:
        lat, lon = 31.95, 35.93

    try:
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": lat,
            "longitude": lon,

            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation"
            ],

            "daily": [
                "et0_fao_evapotranspiration"
            ],

            "timezone": "Asia/Amman",
            "forecast_days": 1
        }

        data = requests.get(
            url,
            params=params,
            timeout=5
        ).json()

        return {
            "location": location,

            "temperature_c":
                data["current"]["temperature_2m"],

            "humidity_percent":
                data["current"]["relative_humidity_2m"],

            "precipitation_mm":
                data["current"]["precipitation"],

            "et0_mm":
                data["daily"]["et0_fao_evapotranspiration"][0],

            "source": "Open-Meteo",
            "data_type": "live_weather"
        }

    except Exception as e:
        return {
            "error": "Weather data unavailable",
            "details": str(e)
        }

# -------------------------------------------------------------
# 2. Resource Tool (إضافة الفلفل لحسابات التكاليف والمياه)
# -------------------------------------------------------------
@tool
def calculate_crop_resources(crop: str, dunums: float):
    """Calculate crop water, production and reference cost."""

    import json

    aliases = {
        "أسود عجمي": "باذنجان",
        "أسود كلاسيك": "باذنجان",
        "أسود رفيع": "باذنجان",
        "بندورة معلقة": "بندورة",
        "موز بلدي قطوف": "موز بلدي",
        "موز بلدي كرتون": "موز بلدي"
    }

    crop = aliases.get(crop, crop)

    with open("crop_resources.json", "r", encoding="utf-8") as f:
        crop_data = json.load(f)

    data = crop_data.get(crop)

    if not data:
        return {
            "error": f"No resource data for {crop}"
        }

    return {
        "crop": crop,
        "dunums": dunums,

        "water_m3_per_dunum":
            data["water_m3_per_dunum"],

        "total_water_m3":
            data["water_m3_per_dunum"] * dunums,

        "yield_kg_per_dunum":
            data["yield_kg_per_dunum"],

        "expected_production_kg":
            data["yield_kg_per_dunum"] * dunums,

        "historical_operating_cost_jod_per_dunum":
            data["historical_operating_cost_jod_per_dunum"],

        "historical_operating_cost_jod":
            data["historical_operating_cost_jod_per_dunum"] * dunums,

        "cost_type": "historical_reference"
    }
# -------------------------------------------------------------
# 3. Market Tool (إضافة أسعار الفلفل في الحسبة)
# -------------------------------------------------------------
import json

@tool
def get_market_prices(crop: str, market: str):
    """Get latest crop prices for Amman or Irbid."""

    with open("market_prices.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    market_names = {
        "عمان": "amman",
        "عمّان": "amman",
        "amman": "amman",

        "اربد": "irbid",
        "إربد": "irbid",
        "irbid": "irbid"
    }

    market = market_names.get(market.strip().lower())

    if not market:
        return {"error": "Market must be Amman or Irbid"}

    return data[market]["crops"].get(
        crop,
        {"error": f"Crop {crop} not found in {market}"}
    )


@tool
def optimize_farm_plan(
    total_dunums: int,
    budget_jod: float,
    crops_to_consider: list[str] | None = None
):
    """
    Optimize a ONE-SEASON farm plan.

    Returns:
    - highest margin plan
    - best water efficiency plan
    - balanced plan

    If crops_to_consider is not provided, all supported seasonal crops
    with enough data are compared automatically.
    """

    import json

    # ==========================================
    # Load data
    # ==========================================

    with open("crop_resources.json", "r", encoding="utf-8") as f:
        resources = json.load(f)

    with open("market_prices.json", "r", encoding="utf-8") as f:
        markets = json.load(f)


    # ==========================================
    # Crops that should NOT be compared with
    # one-season vegetable crops
    # ==========================================

    perennial_crops = {
        "تفاح",
        "تفاح محلي",
        "ليمون",
        "ليمون محلي",
        "موز",
        "موز بلدي",
        "موز بلدي قطوف",
        "موز بلدي كرتون"
    }


    # ==========================================
    # If user didn't specify crops:
    # compare all available crops
    # ==========================================

    if not crops_to_consider:
        crops_to_consider = list(resources.keys())


    # ==========================================
    # Find best currently available market price
    # ==========================================

    def best_price(crop):

        available_prices = []

        amman_crop = (
            markets
            .get("amman", {})
            .get("crops", {})
            .get(crop)
        )

        irbid_crop = (
            markets
            .get("irbid", {})
            .get("crops", {})
            .get(crop)
        )


        if amman_crop:

            price = amman_crop.get(
                "representative_price_jod_per_kg"
            )

            if price is not None:

                available_prices.append({
                    "market": "amman",
                    "price": price
                })


        if irbid_crop:

            price = irbid_crop.get(
                "representative_price_jod_per_kg"
            )

            if price is not None:

                available_prices.append({
                    "market": "irbid",
                    "price": price
                })


        if not available_prices:
            return None


        return max(
            available_prices,
            key=lambda x: x["price"]
        )


    # ==========================================
    # Validate crops
    # ==========================================

    valid_crops = []
    ignored_crops = []


    for crop in crops_to_consider:

        # Don't mix orchard/perennial crops
        # with one-season vegetable planning
        if crop in perennial_crops:

            ignored_crops.append({
                "crop": crop,
                "reason": (
                    "perennial crop excluded from "
                    "one-season optimization"
                )
            })

            continue


        if crop not in resources:

            ignored_crops.append({
                "crop": crop,
                "reason": "missing resource data"
            })

            continue


        crop_data = resources[crop]


        if crop_data.get(
            "historical_operating_cost_jod_per_dunum"
        ) is None:

            ignored_crops.append({
                "crop": crop,
                "reason": "missing reference cost data"
            })

            continue


        if crop_data.get(
            "water_m3_per_dunum"
        ) is None:

            ignored_crops.append({
                "crop": crop,
                "reason": "missing water data"
            })

            continue


        if crop_data.get(
            "yield_kg_per_dunum"
        ) is None:

            ignored_crops.append({
                "crop": crop,
                "reason": "missing yield data"
            })

            continue


        if best_price(crop) is None:

            ignored_crops.append({
                "crop": crop,
                "reason": "missing reliable market price"
            })

            continue


        valid_crops.append(crop)


    if not valid_crops:

        return {
            "success": False,
            "message": (
                "No seasonal crops have enough data "
                "for optimization."
            ),
            "ignored_crops": ignored_crops
        }


    # ==========================================
    # Allocation size
    # ==========================================

    step = 10


    if total_dunums <= 0:

        return {
            "success": False,
            "message": "Total dunums must be greater than zero."
        }


    if total_dunums % step != 0:

        return {
            "success": False,
            "message": (
                "For the current MVP, total dunums "
                "must be divisible by 10."
            )
        }


    units = total_dunums // step


    # ==========================================
    # Generate every possible allocation
    # ==========================================

    def generate_allocations(
        number_of_crops,
        remaining_units
    ):

        if number_of_crops == 1:

            yield [remaining_units]

            return


        for i in range(remaining_units + 1):

            for rest in generate_allocations(
                number_of_crops - 1,
                remaining_units - i
            ):

                yield [i] + rest


    valid_plans = []


    # ==========================================
    # Evaluate allocations
    # ==========================================

    for allocation_units in generate_allocations(
        len(valid_crops),
        units
    ):

        allocation = {}

        total_cost = 0
        total_water = 0
        total_revenue = 0
        total_production = 0


        for crop, crop_units in zip(
            valid_crops,
            allocation_units
        ):

            dunums = crop_units * step


            if dunums == 0:
                continue


            crop_data = resources[crop]

            market_data = best_price(crop)


            cost_per_dunum = crop_data[
                "historical_operating_cost_jod_per_dunum"
            ]

            water_per_dunum = crop_data[
                "water_m3_per_dunum"
            ]

            yield_per_dunum = crop_data[
                "yield_kg_per_dunum"
            ]

            market_price = market_data["price"]


            # ----------------------------------
            # Calculate crop numbers
            # ----------------------------------

            production = (
                yield_per_dunum
                * dunums
            )

            cost = (
                cost_per_dunum
                * dunums
            )

            water = (
                water_per_dunum
                * dunums
            )

            revenue = (
                production
                * market_price
            )


            total_cost += cost
            total_water += water
            total_revenue += revenue
            total_production += production


            allocation[crop] = {

                "dunums":
                    dunums,

                "expected_production_kg":
                    round(production, 2),

                "water_m3":
                    round(water, 2),

                "reference_cost_jod":
                    round(cost, 2),

                "price_preferred_market":
                    market_data["market"],

                "representative_market_price_jod_per_kg":
                    market_price,

                "estimated_revenue_jod":
                    round(revenue, 2)
            }


        # ======================================
        # Budget constraint
        # ======================================

        if total_cost > budget_jod:
            continue


        if total_water <= 0:
            continue


        estimated_margin = (
            total_revenue
            - total_cost
        )


        water_efficiency = (
            estimated_margin
            / total_water
        )


        valid_plans.append({

            "allocation":
                allocation,

            "total_cost_jod":
                round(total_cost, 2),

            "remaining_budget_jod":
                round(
                    budget_jod - total_cost,
                    2
                ),

            "total_water_m3":
                round(total_water, 2),

            "total_production_kg":
                round(total_production, 2),

            "estimated_revenue_jod":
                round(total_revenue, 2),

            "estimated_margin_jod":
                round(estimated_margin, 2),

            "water_efficiency_jod_per_m3":
                round(water_efficiency, 3)
        })


    # ==========================================
    # No valid plans
    # ==========================================

    if not valid_plans:

        return {
            "success": False,
            "message": (
                "No valid crop allocation fits "
                "the available budget."
            ),
            "crops_considered": valid_crops,
            "ignored_crops": ignored_crops
        }


    # ==========================================
    # Highest margin
    # ==========================================

    highest_margin_plan = max(
        valid_plans,
        key=lambda plan:
            plan["estimated_margin_jod"]
    )


    # ==========================================
    # Best water efficiency
    # ==========================================

    best_water_efficiency_plan = max(
        valid_plans,
        key=lambda plan:
            plan["water_efficiency_jod_per_m3"]
    )


    # ==========================================
    # Balanced plan
    #
    # Must keep at least 90% of maximum margin.
    # Among those plans, choose lowest water use.
    # ==========================================

    minimum_acceptable_margin = (
        highest_margin_plan[
            "estimated_margin_jod"
        ]
        * 0.90
    )


    profitable_plans = [

        plan

        for plan in valid_plans

        if plan["estimated_margin_jod"]
        >= minimum_acceptable_margin
    ]


    balanced_plan = min(
        profitable_plans,
        key=lambda plan:
            plan["total_water_m3"]
    )


    # ==========================================
    # Return result
    # ==========================================

    return {

        "success": True,

        "optimization_type":
            "one-season seasonal crop planning",

        "crops_considered":
            valid_crops,

        "plans_evaluated":
            len(valid_plans),

        "highest_margin_plan":
            highest_margin_plan,

        "best_water_efficiency_plan":
            best_water_efficiency_plan,

        "balanced_plan":
            balanced_plan,

        "ignored_crops":
            ignored_crops,

        "important_notes": [
            (
                "Market prices are current market snapshots "
                "and are not guaranteed future harvest prices."
            ),
            (
                "Estimated margin is a planning estimate "
                "using reference operating costs and is not "
                "guaranteed net profit."
            ),
            (
                "Perennial orchard crops are excluded because "
                "they are not directly comparable with "
                "one-season crop decisions."
            )
        ]
    }