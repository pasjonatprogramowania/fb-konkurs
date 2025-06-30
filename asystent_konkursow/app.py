
import streamlit as st
import pandas as pd

# Initialize session state variables if they don't exist
# For input fields
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""
if 'search_phrase' not in st.session_state:
    st.session_state.search_phrase = ""
if 'scroll_count' not in st.session_state:
    st.session_state.scroll_count = 5 # Default value as per spec

# For button clicks (to avoid re-triggering on rerun without interaction)
if 'start_button_clicked' not in st.session_state:
    st.session_state.start_button_clicked = False
if 'save_button_clicked' not in st.session_state:
    st.session_state.save_button_clicked = False

# --- Sidebar ---
with st.sidebar:
    st.header("Konfiguracja")
    # Using st.session_state directly for text_input's default doesn't work as expected for updates.
    # Instead, we can manage it by assigning the widget to a variable and then updating session_state,
    # or by using a callback. For simplicity, Streamlit handles state for input widgets using their key.
    # The value will be available in st.session_state.gemini_api_key.
    st.text_input(
        "Klucz API Gemini",
        type="password",
        key="gemini_api_key_input", # Use a different key for the widget if needed for on_change
        value=st.session_state.gemini_api_key,
        on_change=lambda: st.session_state.update(gemini_api_key=st.session_state.gemini_api_key_input)
    )

    st.info(
        "Informacja: Aplikacja otworzy nowe okno przeglądarki w celu wyszukiwania postów. "
        "Może być konieczne ręczne zalogowanie się do Facebooka w tym oknie."
    )
    st.caption("Pamiętaj, aby nie udostępniać swojego klucza API Gemini.")

# --- Main Application Area ---
st.title("🤖 Asystent Konkursów")

st.subheader("Rozpocznij Wyszukiwanie")
# Search phrase input
st.text_input(
    "Wpisz frazę do wyszukania (np. 'konkurs', 'wygraj', 'rozdanie')",
    key="search_phrase_input",
    value=st.session_state.search_phrase,
    on_change=lambda: st.session_state.update(search_phrase=st.session_state.search_phrase_input)
)

# Scroll count slider
st.slider(
    "Ile razy przewinąć stronę w dół? (więcej przewinięć = więcej postów)",
    min_value=1,
    max_value=20,
    key="scroll_count_input",
    value=st.session_state.scroll_count,
    on_change=lambda: st.session_state.update(scroll_count=st.session_state.scroll_count_input)
)

# Start button
if st.button("Start!", key="start_button"):
    st.session_state.start_button_clicked = True
    st.session_state.save_button_clicked = False # Reset save button state

# Placeholder for future content. This is where button logic will go.
st.markdown("---") # Separator

if st.session_state.start_button_clicked:
    # Retrieve values from session state (which were updated by on_change callbacks)
    api_key = st.session_state.gemini_api_key
    search_phrase_value = st.session_state.search_phrase
    scroll_count_value = st.session_state.scroll_count

    if not api_key:
        st.error("Proszę wprowadzić klucz API Gemini w panelu bocznym.")
        st.session_state.start_button_clicked = False # Reset button state to allow re-click after fixing
    elif not search_phrase_value:
        st.warning("Proszę wpisać frazę do wyszukania.")
        st.session_state.start_button_clicked = False # Reset button state
    else:
        with st.spinner(f"Rozpoczynam wyszukiwanie dla frazy: '{search_phrase_value}' (przewijanie: {scroll_count_value}x)... \n(To jest placeholder - faktyczne przetwarzanie nie jest jeszcze zaimplementowane)"):
            # Simulate work by adding a delay (optional, for testing spinner)
            import time
            time.sleep(3)

            # Placeholder for actual scraper and AI processing logic
            st.success(f"Placeholder: Wyszukiwanie dla '{search_phrase_value}' zakończone (symulacja).")
            st.write("Dane wejściowe:")
            st.json({
                "Klucz API (długość)": len(api_key) if api_key else 0,
                "Fraza wyszukiwania": search_phrase_value,
                "Liczba przewinięć": scroll_count_value
            })
            # In a real scenario, here you would call scraper, then ai_processor,
            # and then update a DataFrame in session_state to be shown by the data_editor.
            # For now, we'll just reset the button state.
            st.session_state.start_button_clicked = False

# Initialize session_state for results DataFrame if it doesn't exist
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame({
        "Link": pd.Series(dtype='str'),
        "Treść Posta": pd.Series(dtype='str'),
        "Zadanie Konkursowe": pd.Series(dtype='str'),
        "Miejsce Zgłoszenia": pd.Series(dtype='str'),
        "Termin Zakończenia": pd.Series(dtype='str')
    })
if 'data_editor_edited_rows' not in st.session_state: # To store edits from data_editor
    st.session_state.data_editor_edited_rows = {}


# --- Results Section ---
st.subheader("Wyniki Analizy")

# Display the data editor. It will be populated from st.session_state.results_df.
# The data_editor widget itself handles edits and stores them in its own internal state,
# which can be accessed via its key in st.session_state (e.g., st.session_state.data_editor)
# For saving, we'll want to react to changes in st.session_state.data_editor (the edited DataFrame)
edited_df = st.data_editor(
    st.session_state.results_df,
    key="data_editor_widget", # Use a specific key for the widget state
    disabled=st.session_state.results_df.empty, # Disable if no data
    num_rows="dynamic",
    # on_change callback for data_editor can be used if needed for immediate reactions,
    # but for a save button, we usually retrieve the state when the button is clicked.
)

# When the data_editor changes, Streamlit reruns. The `edited_df` variable will hold the current state.
# We can assign this back to session_state if we want to persist edits across other interactions
# before explicitly saving. Or, directly use `st.session_state.data_editor_widget` in save logic.
if not st.session_state.results_df.equals(edited_df): # Check if df has changed
     st.session_state.results_df = edited_df # Keep results_df updated with edits

# Save button logic
if st.button("Zapisz zmiany do Excela", key="save_button", disabled=st.session_state.results_df.empty):
    st.session_state.save_button_clicked = True
    st.session_state.start_button_clicked = False

if st.session_state.save_button_clicked and not st.session_state.results_df.empty:
    try:
        # In a real scenario, we'd use st.session_state.results_df which contains the edits.
        # The spec mentions `edited_df = st.session_state.data_editor` - this refers to the
        # state of the data_editor component. The key used for st.data_editor is "data_editor_widget".
        # So, st.session_state.data_editor_widget will contain the edited DataFrame.
        df_to_save = st.session_state.data_editor_widget # This holds the current state of the data editor

        # Create data directory if it doesn't exist
        import os
        output_dir = "data"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, "konkursy_wyniki.xlsx")

        with st.spinner(f"Zapisywanie zmian do {output_path}... (placeholder)"):
            # Placeholder: Simulate saving
            time.sleep(2)
            # df_to_save.to_excel(output_path, index=False) # Actual save operation
            st.success(f"Placeholder: Zmiany zostałyby zapisane do {output_path}")
            # st.write(df_to_save) # Optional: display the df that would be saved

    except Exception as e:
        st.error(f"Błąd podczas zapisywania zmian (placeholder): {e}")
    finally:
        st.session_state.save_button_clicked = False # Reset button state

if __name__ == '__main__':
    # This block is not strictly necessary for Streamlit apps but can be useful.
    # Streamlit apps are run with `streamlit run app.py`
    pass

