import csv
import hmac
import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
CONTENT_FILE = DATA_DIR / "content.json"
PRICE_LIST_FILE = DATA_DIR / "price_list.csv"

CSV_COLUMNS = ("מגזר", "מוצר", "מחיר", "משקל")


def load_content() -> dict:
    if CONTENT_FILE.exists():
        with CONTENT_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    return {
        "title": "ריקשה — מחירון",
        "subtitle": "",
        "currency_name": "מטבע",
        "last_updated": None,
    }


def save_content(content: dict) -> None:
    content["last_updated"] = datetime.now(timezone.utc).isoformat()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CONTENT_FILE.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=2, ensure_ascii=False)
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
    if "currency_amount" not in st.session_state:
        st.session_state.currency_amount = 0.0


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


def render_sidebar(content: dict, items: list[dict]) -> None:
    currency_name = content.get("currency_name", "מטבע")

    with st.sidebar:
        st.header("גישה")
        if is_admin():
            st.success("מחובר כמנהל")
            if st.button("התנתק"):
                logout()
                st.rerun()
        else:
            st.caption("צופים רואים את המחירון. מנהלים יכולים לערוך מחירים.")
            password = st.text_input("סיסמת מנהל", type="password")
            if st.button("כניסה"):
                if try_login(password):
                    st.rerun()
                else:
                    st.error("סיסמה שגויה.")

        st.divider()
        st.header("המרת מטבע")
        st.session_state.currency_amount = st.number_input(
            f"יתרת {currency_name}",
            min_value=0.0,
            value=float(st.session_state.currency_amount),
            step=1.0,
        )

        total_price, total_weight, lines = cart_total(items)
        remaining = st.session_state.currency_amount - total_price

        st.metric("סה״כ בעגלה", f"{total_price:.2f}")
        st.metric("נשאר", f"{remaining:.2f}", delta=None if remaining >= 0 else f"{remaining:.2f}")

        if total_weight > 0:
            st.caption(f"משקל כולל: {total_weight:.1f}")

        if lines:
            st.subheader("פריטים שנבחרו")
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


def render_price_list(items: list[dict], editable: bool) -> None:
    categories = sorted({item["מגזר"] for item in items if item["מגזר"]})
    selected_category = st.selectbox("סינון לפי מגזר", ["הכל"] + categories)
    search = st.text_input("חיפוש מוצר")

    filtered = items
    if selected_category != "הכל":
        filtered = [item for item in filtered if item["מגזר"] == selected_category]
    if search.strip():
        query = search.strip().lower()
        filtered = [item for item in filtered if query in item["מוצר"].lower() or query in item["מגזר"].lower()]

    if editable:
        render_admin_editor(filtered, items)
        return

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


def render_admin_editor(filtered: list[dict], all_items: list[dict]) -> None:
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

    col_save, col_add = st.columns(2)
    with col_save:
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

    with col_add:
        if st.button("הוסף שורה ריקה"):
            all_items.append(
                {
                    "מגזר": filtered[0]["מגזר"] if filtered else "כללי",
                    "מוצר": "מוצר חדש",
                    "מחיר": "0",
                    "מחיר_מספרי": 0.0,
                    "משקל": 0.0,
                }
            )
            save_price_list(all_items)
            st.rerun()

    st.divider()
    st.subheader("הגדרות עמוד")
    content = load_content()
    content["title"] = st.text_input("כותרת", value=content.get("title", ""))
    content["subtitle"] = st.text_area("תת-כותרת", value=content.get("subtitle", ""))
    content["currency_name"] = st.text_input(
        "שם המטבע",
        value=content.get("currency_name", "מטבע"),
    )
    if st.button("שמור הגדרות"):
        save_content(content)
        st.success("ההגדרות נשמרו.")


def main() -> None:
    st.set_page_config(page_title="ריקשה — מחירון", page_icon="🪵", layout="wide")
    init_session_state()

    content = load_content()
    items = load_price_list()

    render_sidebar(content, items)

    st.title(content.get("title", "ריקשה — מחירון"))
    if content.get("subtitle"):
        st.markdown(content["subtitle"])

    if not items:
        st.warning("לא נמצא קובץ מחירון. הוסיפו את `data/price_list.csv`.")
        return

    render_price_list(items, editable=is_admin())

    if content.get("last_updated"):
        st.caption(f"עודכן לאחרונה: {content['last_updated']}")


if __name__ == "__main__":
    main()
