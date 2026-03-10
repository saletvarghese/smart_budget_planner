from flask import Flask, render_template, request, redirect
import pandas as pd
import os
from datetime import datetime

import matplotlib
matplotlib.use('Agg')   # Fix for Tkinter error in Flask

import matplotlib.pyplot as plt

app = Flask(__name__)

DATA_FILE = "budget_history.csv"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/result', methods=['POST'])
def result():

    income = float(request.form['income'])

    categories = request.form.getlist('category')
    amounts = request.form.getlist('amount')

    expenses = {}

    for i in range(len(categories)):
        if categories[i] and amounts[i]:
            expenses[categories[i]] = float(amounts[i])

    total_expense = sum(expenses.values())
    balance = income - total_expense

    # -----------------------------
    # EXPENSE ANALYSIS USING PANDAS
    # -----------------------------
    df = pd.DataFrame(list(expenses.items()), columns=["Category", "Amount"])
    df["Percentage"] = (df["Amount"] / total_expense) * 100
    summary_table = df.to_dict(orient="records")

    highest_row = df.loc[df["Amount"].idxmax()]
    highest_category = highest_row["Category"]
    highest_percentage = highest_row["Percentage"]

    # -----------------------------
    # SMART BUDGET SUGGESTIONS
    # -----------------------------
    suggestions = []
    if highest_percentage > 40:
        suggestions.append(f"You are spending too much on {highest_category}. Try reducing it.")

    savings_rate = (balance / income) * 100
    if savings_rate < 20:
        suggestions.append("Your savings rate is low. Try saving at least 20% of your income.")
    else:
        suggestions.append("Good job! Your savings rate is healthy.")

    # -----------------------------
    # SAVE BUDGET HISTORY
    # -----------------------------
    history_data = {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Income": income,
        "Expense": total_expense,
        "Balance": balance
    }
    history_df = pd.DataFrame([history_data])
    if os.path.exists(DATA_FILE):
        history_df.to_csv(DATA_FILE, mode='a', header=False, index=False)
    else:
        history_df.to_csv(DATA_FILE, index=False)

    # -----------------------------
    # CREATE PIE CHART
    # -----------------------------
    labels = list(expenses.keys())
    values = list(expenses.values())

    if not os.path.exists("static"):
        os.makedirs("static")

    plt.figure(figsize=(6,6))
    plt.pie(values, labels=labels, autopct='%1.1f%%')
    plt.title("Expense Distribution")
    plt.savefig("static/chart.png")
    plt.close()

    return render_template(
        "result.html",
        income=income,
        total=total_expense,
        balance=balance,
        summary=summary_table,
        highest=highest_category,
        suggestions=suggestions
    )


@app.route('/history')
def history():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        history = df.to_dict(orient="records")
    else:
        history = []
    return render_template("history.html", history=history)


@app.route('/delete/<int:index>')
def delete(index):
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = df.drop(index)
        df.to_csv(DATA_FILE, index=False)
    return redirect('/history')


if __name__ == "__main__":
    app.run(debug=True)