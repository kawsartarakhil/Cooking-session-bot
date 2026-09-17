import asyncpg

from config import  SQL_PASSWORD, DB_NAME


async def get_connection():
    try:
        connection = await asyncpg.connect(
            host="localhost",
            user='postgres',
            database=DB_NAME,
            password=SQL_PASSWORD,
            port=5432
        )
        return connection
    except Exception as er:
        print("Connection error:", er)


async def init_tables():
    conn = await get_connection()

    try:
        await conn.execute("""

create table if not exists users (
    id serial primary key,
    telegram_id bigint unique not null,
    username varchar(100),
    first_name varchar(100) not null,
    role varchar(20) default 'user' check (role in ('user', 'admin')),
    notifications_enabled boolean default true,
    created_at timestamp default current_timestamp
);


    create table if not exists categories (
        id serial primary key,
        name varchar(100) unique not null,
        photo_file_id varchar(255),
        created_at timestamp default current_timestamp
    );


    create table if not exists recipes (
        id serial primary key,
        category_id integer not null references categories(id) on delete cascade,
        created_by integer references users(id) on delete set null,
        name varchar(150) not null,
        description text,
        photo_file_id varchar(255),
        cooking_time_minutes integer not null check (cooking_time_minutes > 0),
        difficulty varchar(20) not null check (
            difficulty in ('easy', 'medium', 'hard')
        ),
        servings integer not null check (servings > 0),
        is_public boolean default true,
        created_at timestamp default current_timestamp
    );


    create table if not exists ingredients (
        id serial primary key,
        recipe_id integer not null references recipes(id) on delete cascade,
        name varchar(100) not null,
        amount varchar(50) not null,
        unit varchar(30)
    );


    create table if not exists steps (
        id serial primary key,
        recipe_id integer not null references recipes(id) on delete cascade,
        step_number integer not null check (step_number > 0),
        instruction text not null,
        photo_file_id varchar(255),
        timer_seconds integer check (timer_seconds > 0),
        unique (recipe_id, step_number)
    );


    create table if not exists favorites (
        user_id integer not null references users(id) on delete cascade,
        recipe_id integer not null references recipes(id) on delete cascade,
        created_at timestamp default current_timestamp,
        primary key (user_id, recipe_id)
    );


    create table if not exists cooking_sessions (
        id serial primary key,
        user_id integer not null references users(id) on delete cascade,
        recipe_id integer not null references recipes(id) on delete cascade,
        current_step integer default 1 check (current_step > 0),
        status varchar(20) not null default 'active' check (
            status in ('active', 'paused', 'completed', 'stopped')
        ),
        started_at timestamp default current_timestamp,
        finished_at timestamp,
        total_cooking_seconds integer default 0 check (
            total_cooking_seconds >= 0
        )
    );


    create table if not exists cooking_timers (
        id serial primary key,
        session_id integer not null references cooking_sessions(id) on delete cascade,
        step_id integer not null references steps(id) on delete cascade,
        started_at timestamp not null,
        ends_at timestamp not null,
        status varchar(20) not null default 'active' check (
            status in ('active', 'completed', 'cancelled')
        ),
        created_at timestamp default current_timestamp,
        check (ends_at > started_at)
    );


    create table if not exists ratings (
        id serial primary key,
        user_id integer not null references users(id) on delete cascade,
        recipe_id integer not null references recipes(id) on delete cascade,
        rating integer not null check (rating between 1 and 5),
        created_at timestamp default current_timestamp,
        unique (user_id, recipe_id)
    );


        """)

        print("tables created")

    except Exception as er:
        print("Initialization error:", er)

    finally:
        await conn.close()