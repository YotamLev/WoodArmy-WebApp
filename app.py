import csv
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from theme import apply_theme, render_banner, render_footer

DATA_DIR = Path(__file__).parent / "data"
CONTENT_FILE = DATA_DIR / "content.json"
INVENTORY_FILE = DATA_DIR / "inventory.json"
PRICE_LIST_FILE = DATA_DIR / "price_list.csv"

CSV_COLUMNS = ("מגזר", "מוצר", "מחיר", "משקל")
EQUIPMENT_COLUMNS = ("פריט", "כמות", "משקל", "הערות")


def load_content() -> dict:
    if CONTENT_FILE.exists():
        with CONTENT_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return {
        "title": "ריקשה — יומן המשלחת",
        "subtitle": "",
        "tagline": "☙ חברת הרייקשה ☙",
        "currency_name": "גילדרים",
        "last_updated": None,
    }


def save_content(content: dict) -> None:
    content["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CONTENT_FILE.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_inventory() -> dict:
    if INVENTORY_FILE.exists():
        with INVENTORY_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return {"money": 0, "equipment": []}


def save_inventory(inventory: dict) -> None:
    inventory["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with INVENTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)
        f.write("\n")


def parse_price(raw: str) -> float | None:
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def load_price_list() -> list[dict]:
    if not PRICE_LIST_FILE.exists():
        return []

    with PRICE_LIST_FILE.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        items = []
        for row in reader:
            price_raw = row.get("מחיר", "").strip()
            numeric_price = parse_price(price_raw)
            weight_raw = row.get("משקל", "").strip()
            weight = float(weight_raw) if weight_raw else 0.0
            items.append(
                {
                    "מגזר": row.get("מגזר", "").strip(),
                    "מוצר": row.get("מוצר", "").strip(),
                    "מחיר": price_raw,
                    "מחיר_מספרי": numeric_price,
                    "משקל": weight,
                }
            )
        return items


def save_price_list(items: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PRICE_LIST_FILE.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "מגזר": item["מגזר"],
                    "מוצר": item["מוצר"],
                    "מחיר": item["מחיר"],
                    "משקל": item["משקל"],
                }
            )


def item_key(item: dict) -> str:
    return f"{item['מגזר']}::{item['מוצר']}"


def get_admin_password() -> str:
    try:
        return st.secrets["ADMIN_PASSWORD"]
    except (KeyError, FileNotFoundError):
        return ""


def is_admin() -> bool:
    return st.session_state.get("is_admin", False)


def try_login(password: str) -> bool:
    expected = get_admin_password()
    if not expected:
        st.error("Admin password is not configured. Add ADMIN_PASSWORD to secrets.")
        return False
    if hmac.compare_digest(password, expected):
        st.session_state.is_admin = True
        return True
    return False


def logout() -> None:
    st.session_state.is_admin = False


def init_session_state() -> None:
    if "cart" not in st.session_state:
        st.session_state.cart = {}


def equipment_total_weight(equipment: list[dict]) -> float:
    total = 0.0
    for row in equipment:
        qty = float(row.get("כמות") or 0)
        weight = float(row.get("משקל") or 0)
        total += qty * weight
    return total


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### מפתח היומן")
        if is_admin():
            st.success("הרשאת עריכה פעילה")
            if st.button("נעילת היומן"):
                logout()
                st.rerun()
        else:
            st.caption("המשלחת קוראת. רק בעלי המפתח יכולים לערוך.")
            password = st.text_input("מפתח המשלחת", type="password")
            if st.button("פתיחת היומן"):
                if try_login(password):
                    st.rerun()
                else:
                    st.error("סיסמה שגויה.")


def render_inventory(content: dict, inventory: dict) -> None:
    currency_name = content.get("currency_name", "גילדרים")
    equipment = inventory.get("equipment", [])
    money = float(inventory.get("money", 0))
    total_weight = equipment_total_weight(equipment)

    if is_admin():
        st.info("מצב עריכה — עדכנו גילדרים וציוד, ואז שמרו ביומן.")

        money = st.number_input(
            f"יתרת {currency_name}",
            min_value=0.0,
            value=money,
            step=1.0,
        )

        edited_equipment = st.data_editor(
            equipment,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "פריט": st.column_config.TextColumn("פריט", required=True),
                "כמות": st.column_config.NumberColumn("כמות", min_value=0, step=1, default=1),
                "משקל": st.column_config.NumberColumn("משקל (ליחידה)", min_value=0.0, step=0.1),
                "הערות": st.column_config.TextColumn("הערות"),
            },
        )

        col_save, col_settings = st.columns(2)
        with col_save:
            if st.button("רישום ביומן", type="primary"):
                cleaned = []
                for row in edited_equipment:
                    name = str(row.get("פריט", "")).strip()
                    if not name:
                        continue
                    cleaned.append(
                        {
                            "פריט": name,
                            "כמות": int(row.get("כמות") or 0),
                            "משקל": float(row.get("משקל") or 0),
                            "הערות": str(row.get("הערות", "")).strip(),
                        }
                    )
                save_inventory({"money": money, "equipment": cleaned})
                st.success("המלאי נשמר.")
                st.rerun()

        with col_settings:
            with st.expander("הגדרות עמוד"):
                content["title"] = st.text_input("כותרת", value=content.get("title", ""))
                content["subtitle"] = st.text_area("תת-כותרת", value=content.get("subtitle", ""))
                content["currency_name"] = st.text_input(
                    "שם המטבע",
                    value=content.get("currency_name", "גילדרים"),
                )
                if st.button("שמור הגדרות"):
                    save_content(content)
                    st.success("ההגדרות נשמרו.")
                    st.rerun()

        return

    col_money, col_weight, col_items = st.columns(3)
    with col_money:
        st.metric(f"יתרת {currency_name}", f"{money:.0f}")
    with col_weight:
        st.metric("משקל כולל", f"{total_weight:.1f}")
    with col_items:
        st.metric("סוגי פריטים", len(equipment))

    if not equipment:
        st.info("התרמילים ריקים — עדיין לא נרשם ציוד.")
        return

    st.markdown('<div class="wa-section-label">ציוד נוכחי</div>', unsafe_allow_html=True)
    st.subheader("מטען המשלחת")
    st.dataframe(
        equipment,
        use_container_width=True,
        hide_index=True,
        column_config={
            "פריט": st.column_config.TextColumn("פריט"),
            "כמות": st.column_config.NumberColumn("כמות"),
            "משקל": st.column_config.NumberColumn("משקל (ליחידה)"),
            "הערות": st.column_config.TextColumn("הערות"),
        },
    )


def cart_total(items: list[dict]) -> tuple[float, float, list[dict]]:
    lookup = {item_key(item): item for item in items}
    total_price = 0.0
    total_weight = 0.0
    lines = []

    for key, quantity in st.session_state.cart.items():
        if quantity <= 0:
            continue
        item = lookup.get(key)
        if not item or item["מחיר_מספרי"] is None:
            continue
        line_price = item["מחיר_מספרי"] * quantity
        line_weight = item["משקל"] * quantity
        total_price += line_price
        total_weight += line_weight
        lines.append(
            {
                "מוצר": item["מוצר"],
                "מגזר": item["מגזר"],
                "כמות": quantity,
                "מחיר ליחידה": item["מחיר_מספרי"],
                "סה״כ": line_price,
                "משקל": line_weight,
            }
        )

    return total_price, total_weight, lines


def render_price_list_admin(all_items: list[dict]) -> None:
    st.info("מצב עריכה — שינויים נשמרים לקובץ המחירון.")

    editor_rows = [
        {
            "מגזר": item["מגזר"],
            "מוצר": item["מוצר"],
            "מחיר": item["מחיר"],
            "משקל": item["משקל"],
        }
        for item in all_items
    ]

    edited = st.data_editor(
        editor_rows,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "מגזר": st.column_config.TextColumn("מגזר", required=True),
            "מוצר": st.column_config.TextColumn("מוצר", required=True),
            "מחיר": st.column_config.TextColumn("מחיר"),
            "משקל": st.column_config.NumberColumn("משקל", min_value=0.0, step=0.1),
        },
    )

    if st.button("שמור מחירון", type="primary"):
        cleaned = []
        for row in edited:
            if not str(row.get("מוצר", "")).strip():
                continue
            price_raw = str(row.get("מחיר", "")).strip()
            cleaned.append(
                {
                    "מגזר": str(row.get("מגזר", "")).strip(),
                    "מוצר": str(row.get("מוצר", "")).strip(),
                    "מחיר": price_raw,
                    "מחיר_מספרי": parse_price(price_raw),
                    "משקל": float(row.get("משקל") or 0),
                }
            )
        save_price_list(cleaned)
        st.success("המחירון נשמר.")
        st.rerun()


def render_shop(content: dict, items: list[dict], inventory: dict) -> None:
    currency_name = content.get("currency_name", "גילדרים")

    if is_admin():
        render_price_list_admin(items)
        st.divider()

    if not items:
        st.warning("לא נמצא קובץ מחירון.")
        return

    st.caption("סחורה מהשוק — הסכום מחושב מול גילדרי המשלחת.")

    available = float(inventory.get("money", 0))
    col_balance, col_cart, col_remaining = st.columns(3)

    total_price, total_weight, lines = cart_total(items)
    remaining = available - total_price

    with col_balance:
        st.metric(f"יתרה במלאי ({currency_name})", f"{available:.0f}")
    with col_cart:
        st.metric("סה״כ בעגלה", f"{total_price:.2f}")
    with col_remaining:
        st.metric("נשאר אחרי רכישה", f"{remaining:.2f}")

    if total_weight > 0:
        st.caption(f"משקל בעגלה: {total_weight:.1f}")

    if lines:
        with st.expander("פריטים שנבחרו", expanded=True):
            for line in lines:
                st.write(f"**{line['מוצר']}** × {line['כמות']} = {line['סה״כ']:.2f}")
        if st.button("נקה עגלה"):
            st.session_state.cart = {}
            st.rerun()
        if total_price > 0:
            if remaining < 0:
                st.error("אין מספיק מטבע לרכישה.")
            else:
                st.success("ניתן לרכוש את כל הפריטים בעגלה.")

    categories = sorted({item["מגזר"] for item in items if item["מגזר"]})
    selected_category = st.selectbox("סינון לפי מגזר", ["הכל"] + categories, key="shop_category")
    search = st.text_input("חיפוש מוצר", key="shop_search")

    filtered = items
    if selected_category != "הכל":
        filtered = [item for item in filtered if item["מגזר"] == selected_category]
    if search.strip():
        query = search.strip().lower()
        filtered = [
            item
            for item in filtered
            if query in item["מוצר"].lower() or query in item["מגזר"].lower()
        ]

    if not filtered:
        st.info("לא נמצאו פריטים.")
        return

    for category in sorted({item["מגזר"] for item in filtered}):
        category_items = [item for item in filtered if item["מגזר"] == category]
        st.subheader(category)

        for item in category_items:
            cols = st.columns([4, 1.2, 1, 1])
            price_label = (
                f"{item['מחיר_מספרי']:.2f}"
                if item["מחיר_מספרי"] is not None
                else item["מחיר"]
            )

            with cols[0]:
                st.write(item["מוצר"])
            with cols[1]:
                st.write(price_label)
            with cols[2]:
                st.write(f"{item['משקל']:.1f}")

            with cols[3]:
                if item["מחיר_מספרי"] is None:
                    st.caption("—")
                else:
                    key = item_key(item)
                    current_qty = int(st.session_state.cart.get(key, 0))
                    qty = st.number_input(
                        "כמות",
                        min_value=0,
                        value=current_qty,
                        step=1,
                        key=f"qty_{key}",
                        label_visibility="collapsed",
                    )
                    if qty != current_qty:
                        if qty == 0:
                            st.session_state.cart.pop(key, None)
                        else:
                            st.session_state.cart[key] = qty


def main() -> None:
    st.set_page_config(page_title="ריקשה — יומן המשלחת", page_icon="🌲", layout="wide")
    apply_theme()
    init_session_state()

    content = load_content()
    inventory = load_inventory()
    items = load_price_list()

    render_sidebar()
    render_banner(content)

    tab_inventory, tab_shop = st.tabs(["מלאי המשלחת", "מחירון הסחורה"])

    with tab_inventory:
        render_inventory(content, inventory)

    with tab_shop:
        render_shop(content, items, inventory)

    updated = inventory.get("last_updated") or content.get("last_updated")
    if updated:
        st.caption(f"נרשם לאחרונה ביומן: {updated}")

    render_footer()


if __name__ == "__main__":
    main()
