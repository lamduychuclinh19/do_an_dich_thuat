"""Mock data for the mock API (replace with real backend)."""

LANGS = ["en"]

# UI strings (GET /api/public/translations/<lang>)
UI = {
    "en": {
        "app_name": "Saigon Food Guide", "choose_language": "Choose your language",
        "choose_language_hint": "You can change it any time.",
        "explore": "Explore", "payment": "Unlock", "nearby": "Closest to you",
        "all_places": "All places", "locate_me": "Find my location",
        "locating": "Getting your location…", "geo_denied": "Location access is blocked. Enable it in your browser settings.",
        "geo_unsupported": "Your browser does not support geolocation.", "distance": "From you",
        "you_are_near": "You are near", "listen": "Listen to the story", "details": "View details",
        "narration": "Narration", "play": "Play", "pause": "Stop", "back": "Back",
        "locked_title": "Narration needs to be unlocked",
        "locked_text": "Pick an hourly pass to hear the story at every place.",
        "packages": "Choose a pass", "pay_now": "Create payment code", "scan_qr": "Scan the code or transfer using the note below",
        "confirm_paid": "I have paid", "active_until": "Unlocked, time left",
        "paid_ok": "Payment received. Enjoy your meal!", "go_explore": "Start exploring",
        "loading": "Loading…", "error": "Something went wrong. Please try again.", "radius": "Trigger radius",
    },
}

# Sample places — coordinates for demo only, replace with real data.
POIS = [
    {
        "id": 1, "latitude": 10.7725, "longitude": 106.6980, "trigger_radius_meters": 80,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Ben Thanh Market", "Ben Thanh Market has stood as a symbol of Saigon since the early twentieth century. Its food hall serves fermented-fish noodle soup, grilled pork vermicelli and a wide range of sweet soups, so you can taste the South in a single lunch."),
        },
    },
    {
        "id": 2, "latitude": 10.7716, "longitude": 106.6918, "trigger_radius_meters": 60,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Huynh Hoa Bakery", "A generously stuffed baguette with pâté, Vietnamese ham and rich butter made this shop famous. Come early to avoid the queue and eat while the crust is still crisp."),
        },
    },
    {
        "id": 3, "latitude": 10.7840, "longitude": 106.6888, "trigger_radius_meters": 70,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Pasteur Pho", "The broth is simmered from bones for hours and scented with cinnamon and star anise, served with bean sprouts and herbs. Saigonese eat pho in the morning, so this is a fine place to start the day."),
        },
    },
    {
        "id": 4, "latitude": 10.7612, "longitude": 106.7024, "trigger_radius_meters": 100,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Vinh Khanh Snail Street", "A street known for seafood and stir-fried snails, liveliest in the evening. Try snails in coconut sauce, scallops with scallion oil, and finish with sugarcane juice."),
        },
    },

    {
        "id": 5, "latitude": 10.7905, "longitude": 106.6907, "trigger_radius_meters": 70,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Banh Xeo Dinh Cong Trang", "Crisp, golden turmeric pancakes filled with shrimp, pork and bean sprouts, wrapped in lettuce and fresh herbs and dipped in sweet fish sauce. The sizzle of the batter hitting the hot pan is part of the experience, so sit near the kitchen if you can."),
        },
    },
    {
        "id": 6, "latitude": 10.7948, "longitude": 106.6808, "trigger_radius_meters": 60,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Ba Ghien Broken Rice", "Broken rice grilled over charcoal with a thick marinated pork chop, shredded pork skin and a fried egg. This is a Saigon classic for a hearty late breakfast or an early dinner."),
        },
    },
    {
        "id": 7, "latitude": 10.7673, "longitude": 106.6932, "trigger_radius_meters": 100,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Bui Vien Walking Street", "The liveliest street in the backpacker district, packed with street stalls selling grilled skewers, fresh spring rolls and iced coffee. It comes alive after dark, so visit in the evening for the full atmosphere."),
        },
    },
    {
        "id": 8, "latitude": 10.7742, "longitude": 106.7035, "trigger_radius_meters": 90,
        "image_url": "", "audio_url": {},
        "translations": {
            "en": ("Nguyen Hue Walking Street", "A wide pedestrian boulevard from City Hall down to the river, lined with cafes and dessert shops. Stop for a Vietnamese iced coffee and watch the city stroll by."),
        },
    },
]

# Hourly rental packages (VND)
PACKAGES = [
    {"id": "h1", "hours": 1, "price_vnd": 20000},
    {"id": "h3", "hours": 3, "price_vnd": 50000},
    {"id": "h24", "hours": 24, "price_vnd": 150000},
]