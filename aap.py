import streamlit as st
import json
import os
from datetime import date, datetime
import pandas as pd

# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(
    page_title="SmartLifeFit",
    page_icon="🥗",
    layout="wide"
)

PROFILE_FILE = "smartlifefit_profile.json"
TODAY_FILE = "smartlifefit_today.json"
HISTORY_FILE = "smartlifefit_history.json"

# ============================================================
# FILE HELPERS
# ============================================================
def load_json(filename, default):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError):
        pass
    return default


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except OSError:
        return False


# ============================================================
# LOAD SAVED DATA
# ============================================================
profile = load_json(PROFILE_FILE, {})

# Migration from previous version, if old profile.json exists
if not profile and os.path.exists("profile.json"):
    old_profile = load_json("profile.json", {})

    if old_profile:
        profile = {
            "name": old_profile.get("name", ""),
            "age": old_profile.get("age", ""),
            "gender": old_profile.get("gender", ""),
            "height": old_profile.get("height", ""),
            "current_weight": old_profile.get(
                "weight",
                old_profile.get("current_weight", "")
            ),
            "fitness_level": old_profile.get(
                "fitness_level",
                ""
            ),
            "diet": old_profile.get(
                "diet",
                ""
            ),
            "allergy": old_profile.get(
                "allergy",
                ""
            ),
            "goal_type": old_profile.get(
                "goal_type",
                ""
            ),
            "target_weight": old_profile.get(
                "target_weight",
                ""
            ),
            "duration": old_profile.get(
                "duration",
                ""
            ),
            "start_weight": old_profile.get(
                "start_weight",
                old_profile.get("weight", "")
            )
        }

history = load_json(HISTORY_FILE, [])
today_data = load_json(TODAY_FILE, {})

# ============================================================
# SESSION STATE
# ============================================================
if "step" not in st.session_state:
    st.session_state.step = 1

if "today_saved" not in st.session_state:
    st.session_state.today_saved = bool(today_data)

if "checkin_saved" not in st.session_state:
    st.session_state.checkin_saved = False

if "completion" not in st.session_state:
    st.session_state.completion = 0

# ============================================================
# CSS
# ============================================================
st.markdown(
    """
    <style>
    .app-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .app-subtitle {
        font-size: 18px;
        opacity: 0.75;
        margin-bottom: 20px;
    }

    .step-box {
        padding: 12px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.25);
        text-align: center;
        margin-bottom: 18px;
    }

    .quote-box {
        padding: 24px;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,0.25);
        text-align: center;
        margin-top: 15px;
    }

    .quote {
        font-size: 22px;
        font-weight: 600;
    }

    .plan-card {
        padding: 18px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HEADER
# ============================================================
st.markdown(
    '<div class="app-title">🥗 SmartLifeFit</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">'
    'Adaptive Personalized Nutrition & Workout Recommender'
    '</div>',
    unsafe_allow_html=True
)

st.write(
    "Set your profile → customize today → get your plan → "
    "complete your day → check your progress."
)

st.divider()

# ============================================================
# STEP INDICATOR
# ============================================================
steps = [
    "👤 Profile",
    "⚙️ Customize",
    "🤖 Today's Plan",
    "✅ End of Day",
    "📈 Progress"
]

current_step = st.session_state.step

step_names = "  →  ".join(
    [
        f"**{i+1}. {name}**" if i + 1 == current_step
        else f"{i+1}. {name}"
        for i, name in enumerate(steps)
    ]
)

st.markdown(
    f'<div class="step-box">{step_names}</div>',
    unsafe_allow_html=True
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def contains_allergy(text, allergy):
    if not allergy:
        return False

    allergy = allergy.strip().lower()

    if allergy in ("none", "no", "no allergy", "n/a"):
        return False

    words = [
        x.strip()
        for x in allergy.replace("/", ",").split(",")
        if x.strip()
    ]

    text = text.lower()

    return any(word in text for word in words)


def calculate_progress(start, current, target, goal):
    try:
        start = float(start)
        current = float(current)
        target = float(target)
    except (ValueError, TypeError):
        return 0, 0

    total = abs(target - start)

    if total == 0:
        return 100, 0

    remaining = abs(target - current)
    progress = 1 - (remaining / total)

    progress = max(0, min(progress, 1))

    return progress * 100, remaining


def goal_text(goal, start, target):
    difference = abs(float(target) - float(start))

    if goal == "Weight Gain":
        return f"Gain {difference:.1f} kg"

    if goal == "Weight Loss":
        return f"Lose {difference:.1f} kg"

    return "Maintain weight"


def get_meal_plan(diet, available_food, goal):
    available = available_food.lower()

    # Breakfast
    if "oats" in available:
        breakfast = "Oats + banana + nuts"
    elif "poha" in available:
        breakfast = "Poha + fruit"
    elif "egg" in available and diet == "Non-Vegetarian":
        breakfast = "Eggs + roti/toast + fruit"
    elif "roti" in available:
        breakfast = "Roti + curd/plant yogurt + fruit"
    elif "banana" in available:
        breakfast = "Banana + oats / simple breakfast"
    else:
        breakfast = "Simple balanced breakfast with a protein source"

    # Lunch
    if "dal" in available and "roti" in available:
        lunch = "Dal + roti + vegetables + curd/plant yogurt"
    elif "dal" in available and "rice" in available:
        lunch = "Dal + rice + vegetables"
    elif "chicken" in available and diet == "Non-Vegetarian":
        lunch = "Chicken + rice/roti + vegetables"
    elif "paneer" in available and diet == "Vegetarian":
        lunch = "Paneer + roti + vegetables"
    else:
        if diet == "Vegan":
            lunch = "Dal/chana/tofu + rice/roti + vegetables"
        elif diet == "Vegetarian":
            lunch = "Dal/paneer + rice/roti + vegetables"
        else:
            lunch = "Protein source + rice/roti + vegetables"

    # Snack
    if "banana" in available:
        snack = "Banana + nuts/roasted chana"
    elif "curd" in available and diet != "Vegan":
        snack = "Curd + fruit"
    else:
        snack = "Fruit + roasted chana/nuts"

    # Dinner
    if diet == "Vegan":
        dinner = "Roti/rice + dal/tofu + vegetables"
    elif diet == "Vegetarian":
        dinner = "Roti/rice + dal/paneer + vegetables"
    else:
        dinner = "Roti/rice + eggs/chicken + vegetables"

    meals = {
        "Breakfast": breakfast,
        "Lunch": lunch,
        "Snack": snack,
        "Dinner": dinner
    }

    # Simple allergy protection
    allergy = profile.get("allergy", "")

    safe_meals = {}

    for meal_name, meal in meals.items():
        if contains_allergy(meal, allergy):
            safe_meals[meal_name] = (
                "Choose a safe alternative without the listed allergen."
            )
        else:
            safe_meals[meal_name] = meal

    return safe_meals


def get_meal_times(day_mode):
    if day_mode == "Normal Day":
        return {
            "Breakfast": "8:00 AM",
            "Lunch": "1:00 PM",
            "Snack": "5:00 PM",
            "Dinner": "8:30 PM"
        }

    if day_mode == "College Day":
        return {
            "Breakfast": "7:30 AM",
            "Lunch": "1:30 PM",
            "Snack": "5:30 PM",
            "Dinner": "8:30 PM"
        }

    if day_mode == "Exam / Assignment Day":
        return {
            "Breakfast": "7:30 AM",
            "Lunch": "12:30 PM",
            "Snack": "4:30 PM",
            "Dinner": "8:00 PM"
        }

    return {
        "Breakfast": "9:00 AM",
        "Lunch": "1:30 PM",
        "Snack": "5:00 PM",
        "Dinner": "8:30 PM"
    }


def get_workout_plan(goal, time_minutes, equipment, energy):
    time_minutes = int(time_minutes)

    # Adapt duration
    if energy == "Low":
        time_minutes = min(time_minutes, 15)

    if time_minutes <= 15:
        duration = "15 minutes"

        if equipment == "Dumbbells":
            exercises = [
                "3 min warm-up",
                "3 min dumbbell squats",
                "3 min dumbbell rows",
                "3 min shoulder press",
                "3 min stretching"
            ]
        elif equipment == "Resistance Bands":
            exercises = [
                "3 min warm-up",
                "3 min band squats",
                "3 min band rows",
                "3 min band press",
                "3 min stretching"
            ]
        else:
            exercises = [
                "3 min warm-up",
                "3 min squats",
                "3 min wall push-ups/push-ups",
                "3 min glute bridge",
                "3 min stretching"
            ]

    elif time_minutes <= 30:
        duration = "30 minutes"

        if equipment == "Dumbbells":
            exercises = [
                "5 min warm-up",
                "7 min goblet squats + lunges",
                "7 min dumbbell rows + shoulder press",
                "6 min core/cardio",
                "5 min stretching"
            ]
        elif equipment == "Resistance Bands":
            exercises = [
                "5 min warm-up",
                "7 min band squats + lunges",
                "7 min band rows + press",
                "6 min core/cardio",
                "5 min stretching"
            ]
        else:
            exercises = [
                "5 min warm-up",
                "7 min squats + lunges",
                "7 min push-ups + glute bridge",
                "6 min cardio",
                "5 min stretching"
            ]

    else:
        duration = f"{time_minutes} minutes"

        if equipment == "Dumbbells":
            exercises = [
                "5 min warm-up",
                "10 min lower-body strength",
                "10 min upper-body dumbbell strength",
                "10 min core/cardio",
                "5 min stretching"
            ]
        elif equipment == "Resistance Bands":
            exercises = [
                "5 min warm-up",
                "10 min lower-body band work",
                "10 min upper-body band work",
                "10 min core/cardio",
                "5 min stretching"
            ]
        else:
            exercises = [
                "5 min warm-up",
                "10 min strength exercises",
                "10 min lower body",
                "10 min upper body/core",
                "5 min stretching"
            ]

    if goal == "Weight Gain":
        focus = "Strength-focused routine with controlled cardio."
    elif goal == "Weight Loss":
        focus = "Strength + moderate cardio routine."
    else:
        focus = "Balanced strength + cardio routine."

    return duration, exercises, focus


# ============================================================
# STEP 1 — PROFILE
# ============================================================
if current_step == 1:

    st.header("👤 Step 1 — Set Your Profile")

    st.write(
        "First create your profile. "
        "Your saved details will appear automatically next time."
    )

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input(
            "Name",
            value=str(profile.get("name", ""))
        )

        age_text = st.text_input(
            "Age",
            value=str(profile.get("age", ""))
        )

        gender_options = [
            "Select",
            "Female",
            "Male",
            "Other"
        ]

        saved_gender = profile.get("gender", "Select")

        if saved_gender not in gender_options:
            saved_gender = "Select"

        gender = st.selectbox(
            "Gender",
            gender_options,
            index=gender_options.index(saved_gender)
        )

        height_text = st.text_input(
            "Height (cm)",
            value=str(profile.get("height", ""))
        )

        current_weight_text = st.text_input(
            "Current Weight (kg)",
            value=str(
                profile.get(
                    "current_weight",
                    profile.get("weight", "")
                )
            )
        )

    with col2:

        fitness_options = [
            "Select",
            "Beginner",
            "Intermediate",
            "Advanced"
        ]

        saved_fitness = profile.get(
            "fitness_level",
            "Select"
        )

        if saved_fitness not in fitness_options:
            saved_fitness = "Select"

        fitness_level = st.selectbox(
            "Fitness Level",
            fitness_options,
            index=fitness_options.index(
                saved_fitness
            )
        )

        diet_options = [
            "Select",
            "Vegetarian",
            "Non-Vegetarian",
            "Vegan"
        ]

        saved_diet = profile.get(
            "diet",
            "Select"
        )

        if saved_diet not in diet_options:
            saved_diet = "Select"

        diet = st.selectbox(
            "Diet Preference",
            diet_options,
            index=diet_options.index(
                saved_diet
            )
        )

        allergy = st.text_input(
            "Food Allergy",
            value=str(
                profile.get(
                    "allergy",
                    ""
                )
            ),
            placeholder="Type None if there is no allergy"
        )

    st.divider()

    st.subheader("🎯 Your Main Goal")

    goal_options = [
        "Select",
        "Weight Loss",
        "Weight Gain",
        "Maintain Weight"
    ]

    saved_goal = profile.get(
        "goal_type",
        "Select"
    )

    if saved_goal not in goal_options:
        saved_goal = "Select"

    goal_type = st.selectbox(
        "Goal",
        goal_options,
        index=goal_options.index(saved_goal)
    )

    goal_col1, goal_col2 = st.columns(2)

    with goal_col1:

        target_weight_text = st.text_input(
            "Target Weight (kg)",
            value=str(
                profile.get(
                    "target_weight",
                    ""
                )
            ),
            disabled=(goal_type == "Maintain Weight")
        )

    with goal_col2:

        duration_text = st.text_input(
            "Target Duration (weeks)",
            value=str(
                profile.get(
                    "duration",
                    ""
                )
            )
        )

    st.divider()

    save_col1, save_col2 = st.columns(2)

    with save_col1:

        if st.button(
            "💾 Save Profile & Continue →",
            use_container_width=True
        ):

            age = get_float(age_text)
            height = get_float(height_text)
            current_weight = get_float(
                current_weight_text
            )
            duration = get_float(duration_text)

            if not name.strip():
                st.error("Please enter your name.")

            elif age is None or age <= 0:
                st.error("Please enter a valid age.")

            elif gender == "Select":
                st.error("Please select your gender.")

            elif height is None or height <= 0:
                st.error("Please enter a valid height.")

            elif current_weight is None or current_weight <= 0:
                st.error("Please enter a valid current weight.")

            elif fitness_level == "Select":
                st.error("Please select your fitness level.")

            elif diet == "Select":
                st.error("Please select your diet preference.")

            elif goal_type == "Select":
                st.error("Please select your goal.")

            elif duration is None or duration <= 0:
                st.error("Please enter target duration.")

            else:

                if goal_type == "Maintain Weight":
                    target_weight = current_weight
                else:
                    target_weight = get_float(
                        target_weight_text
                    )

                if target_weight is None or target_weight <= 0:
                    st.error(
                        "Please enter a valid target weight."
                    )

                elif (
                    goal_type == "Weight Gain"
                    and target_weight <= current_weight
                ):
                    st.error(
                        "For Weight Gain, target weight "
                        "should be higher than current weight."
                    )

                elif (
                    goal_type == "Weight Loss"
                    and target_weight >= current_weight
                ):
                    st.error(
                        "For Weight Loss, target weight "
                        "should be lower than current weight."
                    )

                else:

                    # Preserve original start weight
                    # for an already existing goal.
                    previous_goal = profile.get(
                        "goal_type"
                    )

                    if previous_goal == goal_type:
                        start_weight = float(
                            profile.get(
                                "start_weight",
                                current_weight
                            )
                        )
                    else:
                        start_weight = current_weight

                    profile = {
                        "name": name.strip(),
                        "age": int(age),
                        "gender": gender,
                        "height": height,
                        "current_weight": current_weight,
                        "fitness_level": fitness_level,
                        "diet": diet,
                        "allergy": allergy.strip()
                        if allergy.strip()
                        else "None",
                        "goal_type": goal_type,
                        "target_weight": target_weight,
                        "duration": int(duration),
                        "start_weight": start_weight
                    }

                    if save_json(
                        PROFILE_FILE,
                        profile
                    ):
                        st.success(
                            "✅ Profile saved successfully!"
                        )
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error(
                            "Could not save the profile."
                        )

    with save_col2:

        if profile:

            if st.button(
                "🆕 New User / Reset Profile",
                use_container_width=True
            ):
                profile = {}

                if os.path.exists(PROFILE_FILE):
                    os.remove(PROFILE_FILE)

                st.session_state.step = 1
                st.rerun()


# ============================================================
# STEP 2 — CUSTOMIZE TODAY
# ============================================================
elif current_step == 2:

    st.header("⚙️ Step 2 — Customize Today")

    st.write(
        "Tell SmartLifeFit what your day looks like. "
        "Your plan will be created from these choices."
    )

    st.subheader("📅 How is your day today?")

    day_mode = st.radio(
        "Today's situation",
        [
            "Normal Day",
            "College Day",
            "Exam / Assignment Day",
            "Holiday"
        ],
        horizontal=True
    )

    st.divider()

    st.subheader("🏋️ Workout Settings")

    workout_col1, workout_col2 = st.columns(2)

    with workout_col1:

        available_time = st.slider(
            "Available Workout Time",
            min_value=10,
            max_value=120,
            value=30,
            step=5
        )

    with workout_col2:

        equipment = st.selectbox(
            "Equipment Available",
            [
                "No Equipment",
                "Dumbbells",
                "Resistance Bands",
                "Full Gym"
            ]
        )

    energy = st.radio(
        "⚡ How is your energy today?",
        [
            "Low",
            "Medium",
            "High"
        ],
        horizontal=True
    )

    st.divider()

    st.subheader("🍱 Food Available Today")

    available_food = st.text_input(
        "Write foods you already have",
        value=today_data.get(
            "available_food",
            ""
        ),
        placeholder="Example: dal, roti, rice, banana, curd"
    )

    meal_time = st.selectbox(
        "Meal preparation time",
        [
            "5 minutes",
            "10 minutes",
            "20 minutes",
            "30+ minutes"
        ]
    )

    st.divider()

    b1, b2 = st.columns(2)

    with b1:

        if st.button(
            "← Back to Profile",
            use_container_width=True
        ):
            st.session_state.step = 1
            st.rerun()

    with b2:

        if st.button(
            "🤖 Create Today's Plan →",
            use_container_width=True
        ):

            today_data = {
                "date": date.today().strftime(
                    "%d-%m-%Y"
                ),
                "day_mode": day_mode,
                "available_time": available_time,
                "equipment": equipment,
                "energy": energy,
                "available_food": available_food,
                "meal_time": meal_time
            }

            if save_json(
                TODAY_FILE,
                today_data
            ):

                st.session_state.today_saved = True
                st.session_state.step = 3
                st.rerun()

            else:
                st.error(
                    "Could not save today's settings."
                )


# ============================================================
# STEP 3 — TODAY'S PLAN
# ============================================================
elif current_step == 3:

    st.header("🤖 Step 3 — Your Smart Plan")

    if not profile:

        st.warning(
            "Please complete your profile first."
        )

        if st.button("Go to Profile"):
            st.session_state.step = 1
            st.rerun()

    else:

        # Read today's data
        if today_data:
            day_mode = today_data.get(
                "day_mode",
                "Normal Day"
            )

            available_time = today_data.get(
                "available_time",
                30
            )

            equipment = today_data.get(
                "equipment",
                "No Equipment"
            )

            energy = today_data.get(
                "energy",
                "Medium"
            )

            available_food = today_data.get(
                "available_food",
                ""
            )

        else:
            day_mode = "Normal Day"
            available_time = 30
            equipment = "No Equipment"
            energy = "Medium"
            available_food = ""

        goal = profile["goal_type"]

        st.success(
            f"Good morning, {profile['name']} 👋 "
            f"Here is today's personalized plan."
        )

        # ----------------------------------------------------
        # GOAL SUMMARY
        # ----------------------------------------------------
        st.subheader("🎯 Your Goal")

        goal_cols = st.columns(4)

        goal_cols[0].metric(
            "Current",
            f"{profile['current_weight']:.1f} kg"
        )

        goal_cols[1].metric(
            "Target",
            f"{profile['target_weight']:.1f} kg"
        )

        goal_cols[2].metric(
            "Goal",
            goal
        )

        goal_cols[3].metric(
            "Today",
            day_mode
        )

        st.divider()

        # ----------------------------------------------------
        # MEAL PLAN
        # ----------------------------------------------------
        st.header("🍽️ Today's Meal Plan")

        meals = get_meal_plan(
            profile["diet"],
            available_food,
            goal
        )

        times = get_meal_times(
            day_mode
        )

        meal_order = [
            "Breakfast",
            "Lunch",
            "Snack",
            "Dinner"
        ]

        for meal_name in meal_order:

            st.markdown(
                f"""
                <div class="plan-card">
                    <b>{times[meal_name]} — {meal_name}</b><br>
                    {meals[meal_name]}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.info(
            "🍱 Meal suggestions are based on your diet preference "
            "and foods available today. Adjust portions according "
            "to your needs and any professional guidance you follow."
        )

        # ----------------------------------------------------
        # WORKOUT PLAN
        # ----------------------------------------------------
        st.header("🏋️ Today's Workout")

        duration, exercises, focus = get_workout_plan(
            goal,
            available_time,
            equipment,
            energy
        )

        st.write(
            f"**Available time:** {duration}"
        )

        st.write(
            f"**Equipment:** {equipment}"
        )

        st.write(
            f"**Focus:** {focus}"
        )

        for exercise in exercises:
            st.write(
                "✅ " + exercise
            )

        # ----------------------------------------------------
        # WHY THIS PLAN?
        # ----------------------------------------------------
        st.divider()

        st.header("🧠 Why this plan?")

        reason_cols = st.columns(2)

        with reason_cols[0]:

            st.write(
                f"✓ Built for your goal: **{goal}**"
            )

            st.write(
                f"✓ Adjusted for your **{day_mode.lower()}**"
            )

            st.write(
                f"✓ Fits your **{available_time}-minute** window"
            )

        with reason_cols[1]:

            st.write(
                f"✓ Uses **{equipment.lower()}**"
            )

            st.write(
                f"✓ Considers your **{profile['diet'].lower()}** diet"
            )

            st.write(
                f"✓ Considers today's **{energy.lower()} energy**"
            )

        if available_food.strip():
            st.write(
                f"✓ Uses your available food: **{available_food}**"
            )

        st.divider()

        # ----------------------------------------------------
        # BACK / NEXT
        # ----------------------------------------------------
        plan_col1, plan_col2 = st.columns(2)

        with plan_col1:

            if st.button(
                "← Change Today's Settings",
                use_container_width=True
            ):
                st.session_state.step = 2
                st.rerun()

        with plan_col2:

            if st.button(
                "✅ Go to End-of-Day Check-in →",
                use_container_width=True
            ):
                st.session_state.step = 4
                st.rerun()


# ============================================================
# STEP 4 — END OF DAY
# ============================================================
elif current_step == 4:

    st.header("✅ Step 4 — End-of-Day Check-in")

    st.write(
        "Before viewing your progress, tell SmartLifeFit "
        "what you completed today."
    )

    st.divider()

    st.subheader("🍽️ Did you complete today's meals?")

    breakfast_done = st.checkbox(
        "Breakfast completed"
    )

    lunch_done = st.checkbox(
        "Lunch completed"
    )

    snack_done = st.checkbox(
        "Snack completed"
    )

    dinner_done = st.checkbox(
        "Dinner completed"
    )

    st.divider()

    st.subheader("🏋️ Did you complete today's workout?")

    workout_done = st.radio(
        "Workout status",
        [
            "Yes, completed",
            "Partially completed",
            "Not completed"
        ],
        horizontal=True
    )

    st.divider()

    st.subheader("🎯 Today's Goal")

    goal_items = [
        breakfast_done,
        lunch_done,
        snack_done,
        dinner_done,
        workout_done == "Yes, completed"
    ]

    completed = sum(
        1 for item in goal_items if item
    )

    total = len(goal_items)

    completion = int(
        (completed / total) * 100
    )

    st.progress(
        completion / 100
    )

    st.subheader(
        f"Today's Goal Completion: {completion}%"
    )

    if completion == 100:
        st.success(
            "🎉 Excellent! You completed all today's goals."
        )
    elif completion >= 60:
        st.info(
            "👍 Good work! You completed most of today's goals."
        )
    else:
        st.warning(
            "Every small step counts. Tomorrow is another opportunity."
        )

    st.divider()

    st.subheader("⚖️ Update Today's Weight")

    current_saved_weight = profile.get(
        "current_weight",
        ""
    )

    weight_today_text = st.text_input(
        "Today's Weight (kg)",
        value=str(current_saved_weight)
    )

    notes = st.text_area(
        "Anything you want to remember about today?",
        placeholder="Example: Workout felt easy, busy college day..."
    )

    st.divider()

    check_col1, check_col2 = st.columns(2)

    with check_col1:

        if st.button(
            "← Back to Today's Plan",
            use_container_width=True
        ):
            st.session_state.step = 3
            st.rerun()

    with check_col2:

        if st.button(
            "💾 Finish Day & View Progress →",
            use_container_width=True
        ):

            weight_today = get_float(
                weight_today_text
            )

            if weight_today is None or weight_today <= 0:

                st.error(
                    "Please enter a valid weight."
                )

            else:

                today_string = date.today().strftime(
                    "%d-%m-%Y"
                )

                record = {
                    "date": today_string,
                    "weight": weight_today,
                    "completion": completion,
                    "breakfast": breakfast_done,
                    "lunch": lunch_done,
                    "snack": snack_done,
                    "dinner": dinner_done,
                    "workout": workout_done,
                    "notes": notes
                }

                # Replace today's entry if already saved
                history = [
                    item
                    for item in history
                    if item.get("date") != today_string
                ]

                history.append(record)

                profile["current_weight"] = weight_today

                save_json(
                    PROFILE_FILE,
                    profile
                )

                save_json(
                    HISTORY_FILE,
                    history
                )

                st.session_state.completion = completion
                st.session_state.checkin_saved = True
                st.session_state.step = 5

                st.rerun()


# ============================================================
# STEP 5 — PROGRESS
# ============================================================
elif current_step == 5:

    st.header("📈 Step 5 — My Progress")

    if not profile:

        st.warning(
            "Profile not found."
        )

        if st.button("Go to Profile"):
            st.session_state.step = 1
            st.rerun()

    else:

        current_weight = float(
            profile["current_weight"]
        )

        start_weight = float(
            profile.get(
                "start_weight",
                current_weight
            )
        )

        target_weight = float(
            profile["target_weight"]
        )

        goal = profile["goal_type"]

        progress_percent, remaining = calculate_progress(
            start_weight,
            current_weight,
            target_weight,
            goal
        )

        st.subheader(
            f"🎯 {goal_text(goal, start_weight, target_weight)}"
        )

        # ----------------------------------------------------
        # SIMPLE JOURNEY
        # ----------------------------------------------------
        progress_cols = st.columns(3)

        progress_cols[0].metric(
            "Start",
            f"{start_weight:.1f} kg"
        )

        progress_cols[1].metric(
            "Current",
            f"{current_weight:.1f} kg"
        )

        progress_cols[2].metric(
            "Target",
            f"{target_weight:.1f} kg"
        )

        st.progress(
            progress_percent / 100
        )

        st.subheader(
            f"{progress_percent:.1f}% of your goal"
        )

        st.caption(
            f"Remaining: {remaining:.1f} kg"
        )

        # ----------------------------------------------------
        # TODAY'S RESULT
        # ----------------------------------------------------
        st.divider()

        st.subheader("✅ Today's Result")

        today_completion = st.session_state.get(
            "completion",
            0
        )

        if not today_completion and history:

            today_string = date.today().strftime(
                "%d-%m-%Y"
            )

            for item in history:

                if item.get("date") == today_string:

                    today_completion = item.get(
                        "completion",
                        0
                    )

        result_col1, result_col2 = st.columns(2)

        with result_col1:

            st.metric(
                "Today's Completion",
                f"{today_completion}%"
            )

        with result_col2:

            if today_completion == 100:
                st.success("🌟 Full day completed!")
            elif today_completion >= 60:
                st.info("👍 Good progress today!")
            else:
                st.warning("🌱 Keep building your routine.")

        # ----------------------------------------------------
        # MOTIVATION
        # ----------------------------------------------------
        st.divider()

        st.subheader("💬 Today's Motivation")

        if today_completion == 100:

            quote = (
                "You showed up and completed the day. "
                "Keep that momentum going! 🔥"
            )

        elif today_completion >= 60:

            quote = (
                "Progress does not need to be perfect. "
                "Keep moving forward. 🌱"
            )

        else:

            quote = (
                "A difficult day is not the end of your journey. "
                "Start again tomorrow. 💪"
            )

        st.markdown(
            f"""
            <div class="quote-box">
                <div class="quote">
                    🌟 "{quote}"
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ----------------------------------------------------
        # WEIGHT HISTORY
        # ----------------------------------------------------
        st.divider()

        with st.expander("📊 View Weight History"):

            if history:

                rows = []

                for item in history:

                    rows.append(
                        {
                            "Date": item.get(
                                "date",
                                ""
                            ),
                            "Weight (kg)": item.get(
                                "weight",
                                ""
                            ),
                            "Day Completion": (
                                f"{item.get('completion', 0)}%"
                            )
                        }
                    )

                df = pd.DataFrame(rows)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                # Proper date index for graph
                chart_df = pd.DataFrame(
                    [
                        {
                            "Date": datetime.strptime(
                                item["date"],
                                "%d-%m-%Y"
                            ),
                            "Weight": float(
                                item["weight"]
                            )
                        }
                        for item in history
                        if item.get("date")
                        and item.get("weight") is not None
                    ]
                )

                if not chart_df.empty:

                    chart_df = chart_df.sort_values(
                        "Date"
                    )

                    chart_df = chart_df.set_index(
                        "Date"
                    )

                    st.line_chart(
                        chart_df["Weight"]
                    )

            else:

                st.info(
                    "Your weight history will appear here "
                    "after you complete a daily check-in."
                )

        st.divider()

        # ----------------------------------------------------
        # NEXT DAY
        # ----------------------------------------------------
        end_col1, end_col2, end_col3 = st.columns(3)

        with end_col1:

            if st.button(
                "⚙️ Plan Another Day",
                use_container_width=True
            ):

                st.session_state.step = 2
                st.session_state.checkin_saved = False
                st.rerun()

        with end_col2:

            if st.button(
                "👤 Edit Profile",
                use_container_width=True
            ):

                st.session_state.step = 1
                st.rerun()

        with end_col3:

            if st.button(
                "🆕 New User",
                use_container_width=True
            ):

                if os.path.exists(PROFILE_FILE):
                    os.remove(PROFILE_FILE)

                if os.path.exists(TODAY_FILE):
                    os.remove(TODAY_FILE)

                st.session_state.step = 1
                st.session_state.checkin_saved = False

                st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.divider()

st.caption(
    "⚠️ SmartLifeFit provides general wellness guidance "
    "and is not a replacement for professional medical "
    "or nutritional advice."
)