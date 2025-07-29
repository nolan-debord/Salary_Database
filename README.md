# Salary_Database
Database for tracking salaries and cost of living

# How to Run
Start the AWS EC2 instance

ssh -i ~/.ssh/salary_app.pem ubuntu@(the ipv4 Public IP)

git clone https://github.com/nolan-debord/Salary_Database.git
cd Salary_Database

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

git pull origin main

streamlit run streamlit_app.py --server.port 8501 --server.enableCORS false

Website will be http://<Your_Public_IP>:8501
