# Teamwork Challenge: Aurora Serverless v2 + DB Integration

A backend integration guide for deploying and testing a PostgreSQL-compatible Aurora Serverless v2 database for the Teamwork Challenge platform.

## Cloud Database: Aurora Serverless v2

This project uses **AWS Aurora Serverless v2** (PostgreSQL-compatible) for hosting a scalable backend database.

### ✅ Key Features

- Serverless PostgreSQL DB hosted on AWS RDS
- SQLAlchemy-based integration in Python
- Unit test demonstrating connection and data operations
- Environment-based DB configuration using `.env`

---

## Aurora Serverless v2 Setup

To set up Aurora Serverless v2:

1. Go to [AWS RDS Console](https://console.aws.amazon.com/rds)
2. Click **"Create Database"**
3. Choose:
   - Engine: **Amazon Aurora**
   - Edition: **Aurora PostgreSQL-Compatible**
   - Capacity Type: **Serverless v2**
4. Set DB identifier, master username and password
5. Enable **public access** if testing externally
6. Note the endpoint, port, and database name after creation

---

## Environment Configuration

Create a `.env` file at the root of the repository:

```env
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<dbname>
Example: DATABASE_URL=postgresql://admin:mypassword@my-db-host.rds.amazonaws.com:5432/teamwork