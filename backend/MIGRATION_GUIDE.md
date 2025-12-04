# Database Migration Guide

## Initial Setup

After resetting the database, you need to create and apply the initial migration.

### Step 1: Create Initial Migration

From the `backend` directory:

```bash
alembic revision --autogenerate -m "Initial schema: users and roles"
```

This will create a migration file in `alembic/versions/` that includes:
- `users` table with all required columns
- `artists`, `studios`, `models` tables
- Foreign key constraints
- Unique constraints

### Step 2: Review the Migration

Before applying, review the generated migration file to ensure it's correct.

### Step 3: Apply the Migration

```bash
alembic upgrade head
```

This will create all tables in the database.

## Creating New Migrations

When you modify models:

1. Make your changes to the model files
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Description of changes"
   ```
3. Review the generated migration
4. Apply it:
   ```bash
   alembic upgrade head
   ```

## Troubleshooting

If you get errors about tables already existing:
- Make sure you've run the reset script first
- Or manually drop the tables before running migrations

If migrations fail:
- Check that `INKQ_PG_URL` is set correctly
- Verify database connection
- Check migration file for syntax errors

