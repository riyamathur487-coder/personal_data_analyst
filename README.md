# 📊 Personal Data Analyst (Analytica AI)

Welcome to **Analytica AI**, your intelligent, AI-powered Personal Data Assistant! This application enables users to upload datasets and instantly interact with them using natural language. It leverages the lightning-fast **Groq API** and **Llama 3** to provide insights, suggest analyses, and execute code dynamically.

---

## ✨ Features

- **📂 Multi-Format File Support**: Seamlessly upload and read `CSV`, `Excel (.xlsx, .xls)`, and `JSON` files.
- **🤖 AI-Powered Suggestions**: Automatically analyzes your data schema and suggests relevant analytical questions.
- **⚡ Blazing Fast LLM Inference**: Integrated with Groq's API for ultra-fast Llama 3 responses.
- **🐍 Dynamic Code Execution**: The assistant writes and executes Python code securely in the background to answer your queries (using Pandas, Matplotlib, etc.).
- **📈 Data Visualization**: Get interactive charts and plots directly in the web interface.
- **💬 Conversational Interface**: Chat naturally with your data just like you would with a human data analyst.

---

## 🛠️ Tech Stack

- **Frontend/UI**: [Streamlit](https://streamlit.io/)
- **LLM Engine**: [Groq API](https://groq.com/)
- **Data Processing**: Pandas, Python
- **Code Execution**: Custom safe environment logic

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.8+ installed. You will also need a **Groq API Key**.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/riyamathur487-coder/personal_data_analyst.git
   cd personal_data_analyst
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory and add your Groq API key:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```
   The app will automatically open in your default browser at `http://localhost:8501`.

---

## 👨‍💻 Developed By

**RIYA MATHUR**  
*Data Analyst & AI Enthusiast*

---

> Feel free to fork this project, open issues, or submit pull requests. Let's make data analysis accessible to everyone! 🚀


## Deployed Link
[Live link](https://personaldataanalyst-r3kccmhq7cchajpuhfhspo.streamlit.app/)
