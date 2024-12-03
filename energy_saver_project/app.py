from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Global variables to store uploaded dataset and file name
uploaded_data = None
uploaded_file_name = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global uploaded_data, uploaded_file_name
    message = None  # For status feedback

    if request.method == 'POST':
        # Check if the POST request has the file
        if 'file' not in request.files:
            message = "No file part in the request."
            return render_template('index.html', message=message)

        file = request.files['file']

        if file.filename == '':
            message = "No file selected for uploading."
            return render_template('index.html', message=message)

        # Save the file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Load the file into a DataFrame
        try:
            if file.filename.endswith('.csv'):
                uploaded_data = pd.read_csv(file_path)
            elif file.filename.endswith('.xlsx'):
                uploaded_data = pd.read_excel(file_path)
            else:
                message = "Unsupported file type. Please upload a CSV or Excel file."
                return render_template('index.html', message=message)

            uploaded_file_name = file.filename
            message = f"File '{uploaded_file_name}' uploaded successfully!"
        except Exception as e:
            message = f"Error processing the file: {e}"

    return render_template('index.html', message=message, uploaded_file_name=uploaded_file_name)

@app.route('/visualize', methods=['GET'])
def visualize():
    global uploaded_data

    if uploaded_data is None:
        return "No data uploaded. Please upload a dataset first."

    try:
        # Convert Timestamp column to datetime
        if 'Timestamp' in uploaded_data.columns:
            uploaded_data['Timestamp'] = pd.to_datetime(
                uploaded_data['Timestamp'], format='%d-%m-%Y %H.%M', errors='coerce'
            )

        # Add Hour column if Timestamp exists
        if 'Timestamp' in uploaded_data.columns:
            uploaded_data['Hour'] = uploaded_data['Timestamp'].dt.hour

        # Aggregation: Power Consumption by Hour
        if 'Hour' in uploaded_data.columns and 'PowerConsumption_kWh' in uploaded_data.columns:
            hourly_consumption = uploaded_data.groupby('Hour')['PowerConsumption_kWh'].mean().reset_index()

            # Create a Matplotlib plot
            plt.figure(figsize=(10, 5))
            sns.lineplot(x='Hour', y='PowerConsumption_kWh', data=hourly_consumption, marker='o', color='b')
            plt.title("Hourly Average Power Consumption")
            plt.xlabel("Hour of the Day")
            plt.ylabel("Power Consumption (kWh)")
            plot_path = os.path.join("static", "hourly_consumption.png")
            plt.savefig(plot_path)
            plt.close()
        else:
            plot_path = None

        # Create an interactive Plotly visualization
        if 'DeviceType' in uploaded_data.columns and 'DeviceID' in uploaded_data.columns:
            fig = px.sunburst(
                uploaded_data, path=['DeviceType', 'DeviceID'], values='PowerConsumption_kWh',
                color='PowerConsumption_kWh', color_continuous_scale='RdYlGn',
                title="Power Consumption Hierarchy"
            )
            sunburst_html = fig.to_html(full_html=False)
        else:
            sunburst_html = "No DeviceType or DeviceID columns available for visualization."

    except Exception as e:
        return f"An error occurred during visualization: {e}"

    return render_template('index.html', plot_path=plot_path, sunburst_chart=sunburst_html)

if __name__ == '__main__':
    app.run(debug=True)
