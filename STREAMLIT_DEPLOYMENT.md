# Deploying Project P_311 to Streamlit Community Cloud (24/7 Free Hosting)

This guide walks you through deploying **Project P_311: Knowledge driven IoT fault diagnosis assistant** to **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)) so it is live 24/7 at a permanent public URL accessible from any mobile phone, tablet, or PC worldwide with zero server maintenance.

---

## 🚀 Step 1: Create a GitHub Repository and Push

The project is already initialized as a clean Git repository with all necessary files (`streamlit_app.py`, `requirements.txt`, `.streamlit/config.toml`, knowledge base, MQTT modules, etc.) committed.

1. Go to [GitHub](https://github.com/new) and create a **New Repository**:
   - **Repository Name**: `iot-fault-diagnosis-assistant` (or `P_311_IoT_Assistant`)
   - **Visibility**: Public (recommended for free Streamlit Cloud hosting) or Private
   - **Do NOT** check "Add a README" or ".gitignore" (these are already configured locally)
   - Click **Create repository**

2. Copy the remote URL from GitHub (e.g., `https://github.com/<your-username>/iot-fault-diagnosis-assistant.git`) and run these commands in your project folder (`C:\Users\Chinmay\.gemini\antigravity\scratch\P_311_IoT_Fault_Diagnosis_Assistant`):

```bash
git remote add origin https://github.com/<your-username>/iot-fault-diagnosis-assistant.git
git push -u origin main
```

*(If you use GitHub CLI, run `gh auth login` and `gh repo create --source=. --public --push`)*

---

## 🌐 Step 2: Deploy on Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **"New app"** (or **"Create app"**).
3. Fill in the repository details:
   - **Repository**: `<your-username>/iot-fault-diagnosis-assistant`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **App URL**: Choose a custom subdomain (e.g. `iot-fault-p311.streamlit.app`)
4. Expand **Advanced settings > Secrets** to add optional environment variables:
   ```toml
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "your-google-gemini-api-key"
   MQTT_BROKER_HOST = "broker.emqx.io"
   MQTT_BROKER_PORT = 1883
   ```
   *(Note: If you leave `GEMINI_API_KEY` blank, the assistant automatically uses its built-in Expert Knowledge Engine out of the box!)*
5. Click **"Deploy!"**

---

## 📱 Step 3: Access 24/7 from Any Device

Once deployed, your application will be live at:
```
https://<your-app-name>.streamlit.app
```
- Open it on **any smartphone** via cellular 4G/5G.
- Open it on **tablets, laptops, and desktop computers** across any network.
- Runs **24 hours a day, 7 days a week, 365 days a year** with zero downtime or hosting fees!

---

## 💻 Running Streamlit Locally

To run the Streamlit app on your local machine:
```bash
# Option A: Double-click start_streamlit.bat
start_streamlit.bat

# Option B: Run via terminal
streamlit run streamlit_app.py
```
Local dashboard will open immediately at `http://localhost:8501`.
