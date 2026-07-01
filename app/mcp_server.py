# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mcp.server.fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP("HolidayPlannerTools")

@mcp.tool()
def get_weather_forecast(destination: str, date: str) -> str:
    """Get the weather forecast for a destination on a specific date.

    Args:
        destination: The city and country (e.g., 'Paris, France' or 'Tokyo, Japan').
        date: The date of travel (e.g., '2026-07-15').
    """
    dest = destination.lower()
    if "paris" in dest:
        return f"Weather forecast for Paris on {date}: Partly cloudy, 22°C (72°F). 10% chance of rain."
    elif "tokyo" in dest:
        return f"Weather forecast for Tokyo on {date}: Sunny, 26°C (79°F). Humidity 55%. Perfect for sightseeing."
    elif "london" in dest:
        return f"Weather forecast for London on {date}: Light drizzle, 18°C (64°F). Wind 15 km/h. Carry an umbrella."
    elif "new york" in dest:
        return f"Weather forecast for New York on {date}: Clear skies, 28°C (82°F). High UV index."
    else:
        return f"Weather forecast for {destination} on {date}: Mild and pleasant, 21°C (70°F). Mostly sunny."

@mcp.tool()
def get_currency_rate(base_currency: str, target_currency: str) -> str:
    """Get the exchange rate between two currencies.

    Args:
        base_currency: The base currency code (e.g., 'USD', 'EUR', 'GBP').
        target_currency: The target currency code (e.g., 'EUR', 'JPY', 'INR').
    """
    base = base_currency.upper()
    target = target_currency.upper()
    
    rates = {
        ("USD", "EUR"): 0.92,
        ("USD", "GBP"): 0.78,
        ("USD", "JPY"): 155.50,
        ("USD", "INR"): 83.50,
        ("EUR", "GBP"): 0.85,
        ("EUR", "JPY"): 168.20,
        ("GBP", "EUR"): 1.18,
        ("GBP", "JPY"): 198.50,
    }
    
    if base == target:
        return f"1 {base} = 1.00 {target}"
        
    rate = rates.get((base, target))
    if rate is not None:
        return f"Current exchange rate: 1 {base} = {rate:.2f} {target}"
    
    # Reverse lookup
    reverse_rate = rates.get((target, base))
    if reverse_rate is not None:
        rate = 1 / reverse_rate
        return f"Current exchange rate: 1 {base} = {rate:.2f} {target}"
        
    # Default fallback approximation
    return f"Current exchange rate: 1 {base} = 1.25 {target} (Estimated)"

@mcp.tool()
def search_attractions(destination: str, interests: str) -> str:
    """Search for top attractions and points of interest at the destination matching the traveler's interests.

    Args:
        destination: The destination city.
        interests: Comma-separated list of interests (e.g., 'museums, food, nature, adventure').
    """
    dest = destination.lower()
    ints = interests.lower()
    
    attractions = []
    
    if "paris" in dest:
        if "art" in ints or "museum" in ints or "culture" in ints:
            attractions.append("- Louvre Museum (World's largest art museum)")
            attractions.append("- Musée d'Orsay (Impressionist masterpieces)")
        if "history" in ints or "landmark" in ints:
            attractions.append("- Eiffel Tower (Iconic iron lattice tower)")
            attractions.append("- Arc de Triomphe (Historic triumphal arch)")
        if "food" in ints or "shopping" in ints:
            attractions.append("- Champs-Élysées (Luxury shopping and cafes)")
            attractions.append("- Le Marais (Trendy boutiques and historic bakeries)")
    elif "tokyo" in dest:
        if "tech" in ints or "anime" in ints or "shopping" in ints:
            attractions.append("- Akihabara (Electric Town, electronics & anime culture)")
            attractions.append("- Shibuya Crossing & Shibuya Sky (Iconic scramble crossing & observatory)")
        if "history" in ints or "culture" in ints or "temple" in ints:
            attractions.append("- Senso-ji Temple (Tokyo's oldest Buddhist temple in Asakusa)")
            attractions.append("- Meiji Jingu Shrine (Serene Shinto shrine in a forested park)")
        if "nature" in ints or "park" in ints:
            attractions.append("- Shinjuku Gyoen National Garden (Beautiful traditional and greenhouse gardens)")
    else:
        # Generic attractions
        attractions.append(f"- Main City Square & Old Town (Historic center of {destination})")
        attractions.append(f"- Local Food Market (Experience authentic culinary specialties of {destination})")
        attractions.append(f"- Botanical Gardens (Scenic nature walk and relaxation)")
        
    if not attractions:
        attractions.append(f"- Central Landmark (Must-see spot in {destination})")
        attractions.append(f"- City Museum (Learn about local history and culture)")

    result = f"Recommended attractions in {destination} matching '{interests}':\n" + "\n".join(attractions)
    return result

@mcp.tool()
def generate_packing_checklist(destination: str, duration_days: int, weather_summary: str) -> str:
    """Generate a customized packing checklist based on destination, duration, and weather.

    Args:
        destination: The destination.
        duration_days: The number of days of the trip.
        weather_summary: Summary of expected weather (e.g., 'rainy', 'hot', 'cold', 'sunny').
    """
    weather = weather_summary.lower()
    
    # Base items
    checklist = [
        "Essentials:",
        "- Passport, visa, and ID cards",
        "- Flight tickets & hotel booking confirmations",
        "- Debit/credit cards and some local currency",
        "- Phone, chargers, and power adapter/converter",
        "- Essential medications & toiletries",
        "\nClothing:"
    ]
    
    # Clothing based on duration
    shirts = min(duration_days, 7)
    pants = min(max(duration_days // 2, 2), 4)
    checklist.append(f"- {shirts}x shirts/tops")
    checklist.append(f"- {pants}x pants/shorts/skirts")
    checklist.append(f"- Underwear and socks for {duration_days} days")
    checklist.append("- 1x comfortable walking shoes")
    
    # Weather-specific additions
    checklist.append("\nWeather-Specific & Extras:")
    if "rain" in weather or "drizzle" in weather or "wet" in weather:
        checklist.append("- Compact umbrella or raincoat")
        checklist.append("- Waterproof shoes/boots")
    elif "cold" in weather or "snow" in weather or "winter" in weather:
        checklist.append("- Heavy jacket or coat")
        checklist.append("- Thermal base layers")
        checklist.append("- Gloves, scarf, and beanie")
    elif "hot" in weather or "sunny" in weather or "warm" in weather:
        checklist.append("- Sunglasses & sunscreen (SPF 50+)")
        checklist.append("- Sun hat or cap")
        checklist.append("- Swimwear")
    else:
        checklist.append("- Light jacket or sweater (for cooler evenings)")

    return f"Custom Packing Checklist for {duration_days} days in {destination}:\n" + "\n".join(checklist)

if __name__ == "__main__":
    mcp.run()
