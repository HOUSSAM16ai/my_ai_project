"""Upgrade all models to SQLAlchemy 2.0 syntax (Unified Overmind Schema)

Revision ID: 051ce2ba043e
Revises: 
Create Date: 2025-08-25 12:04:29.274736
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# Try to use JSONB on PostgreSQL; fallback to generic JSON otherwise
try:
    from sqlalchemy.dialects import postgresql
    JSONType = postgresql.JSONB
except Exception:
    JSONType = sa.JSON  # Fallback

# revision identifiers, used by Alembic.
revision = '051ce2ba043e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    NOTE:
      - تمت إزالة أي استدعاء لـ app.models.JSONB_or_JSON() لأنه غير متاح داخل بيئة الترحيل.
      - تم فصل إضافة المفتاح الأجنبي (active_plan_id -> mission_plans.id) إلى مرحلة لاحقة بعد إنشاء الجداول.
    """

    # ------------------------------------------------------------------
    # 1) الجداول الأساسية: subjects, users
    # ------------------------------------------------------------------
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_subjects_name', 'subjects', ['name'], unique=True)

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=True),
        sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ------------------------------------------------------------------
    # 2) lessons, exercises (تعتمد subjects)
    # ------------------------------------------------------------------
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=250), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_lessons_subject_id', 'lessons', ['subject_id'])

    op.create_table(
        'exercises',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('question', sa.Text(), nullable=True),
        sa.Column('correct_answer_data', JSONType(), nullable=True),
        sa.Column('lesson_id', sa.Integer(), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_exercises_lesson_id', 'exercises', ['lesson_id'])

    # ------------------------------------------------------------------
    # 3) missions (بدون FK active_plan_id الآن لتفادي مشكلة ترتيب الإنشاء)
    # ------------------------------------------------------------------
    op.create_table(
        'missions',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('objective', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum(
            'PENDING', 'PLANNING', 'PLANNED', 'RUNNING', 'ADAPTING',
            'SUCCESS', 'FAILED', 'CANCELED',
            name='missionstatus', native_enum=False
        ), nullable=False),
        sa.Column('initiator_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('active_plan_id', sa.Integer(), nullable=True),  # FK will be added AFTER mission_plans exists
        sa.Column('locked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('result_summary', sa.Text(), nullable=True),
        sa.Column('total_cost_usd', sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column('adaptive_cycles', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_missions_initiator_id', 'missions', ['initiator_id'])
    op.create_index('ix_missions_status', 'missions', ['status'])

    # ------------------------------------------------------------------
    # 4) mission_plans (يعتمد missions)
    # ------------------------------------------------------------------
    op.create_table(
        'mission_plans',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('planner_name', sa.String(length=120), nullable=True),
        sa.Column('status', sa.Enum(
            'DRAFT', 'VALID', 'SUPERSEDED', 'FAILED',
            name='planstatus', native_enum=False
        ), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('raw_json', JSONType(), nullable=False),
        sa.Column('stats_json', JSONType(), nullable=True),
        sa.Column('warnings_json', JSONType(), nullable=True),
        sa.Column('content_hash', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('mission_id', 'version', name='uq_mission_plan_version')
    )
    op.create_index('ix_mission_plans_mission_id', 'mission_plans', ['mission_id'])
    op.create_index('ix_mission_plans_status', 'mission_plans', ['status'])
    op.create_index('ix_mission_plans_content_hash', 'mission_plans', ['content_hash'])

    # الآن إضافة FK المتأخر (active_plan_id -> mission_plans.id)
    op.create_foreign_key(
        'fk_missions_active_plan_id',
        'missions', 'mission_plans',
        ['active_plan_id'], ['id'],
        use_alter=True
    )

    # ------------------------------------------------------------------
    # 5) submissions (يعتمد exercises + users)
    # ------------------------------------------------------------------
    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('student_answer_data', JSONType(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('exercise_id', sa.Integer(), sa.ForeignKey('exercises.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_submissions_user_id', 'submissions', ['user_id'])
    op.create_index('ix_submissions_exercise_id', 'submissions', ['exercise_id'])

    # ------------------------------------------------------------------
    # 6) tasks
    # ------------------------------------------------------------------
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('mission_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_key', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.Enum('TOOL', 'SYSTEM', 'META', 'VERIFICATION', name='tasktype', native_enum=False), nullable=False),
        sa.Column('tool_name', sa.String(length=255), nullable=True),
        sa.Column('tool_args_json', JSONType(), nullable=True),
        sa.Column('depends_on_json', JSONType(), nullable=True),
        sa.Column('priority', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('criticality', sa.String(length=20), nullable=True),
        sa.Column('status', sa.Enum(
            'PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'RETRY', 'SKIPPED',
            name='taskstatus', native_enum=False
        ), nullable=False),
        sa.Column('attempt_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default=sa.text('3'), nullable=False),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_text', sa.Text(), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', JSONType(), nullable=True),
        sa.Column('cost_usd', sa.Numeric(precision=12, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_task_mission_status', 'tasks', ['mission_id', 'status'])
    op.create_index('ix_task_plan_taskkey', 'tasks', ['plan_id', 'task_key'])
    op.create_index('ix_tasks_mission_id', 'tasks', ['mission_id'])
    op.create_index('ix_tasks_plan_id', 'tasks', ['plan_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_task_key', 'tasks', ['task_key'])
    op.create_index('ix_tasks_task_type', 'tasks', ['task_type'])
    op.create_index('ix_tasks_tool_name', 'tasks', ['tool_name'])

    # ------------------------------------------------------------------
    # 7) mission_events
    # ------------------------------------------------------------------
    op.create_table(
        'mission_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('mission_id', sa.Integer(), sa.ForeignKey('missions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.Enum(
            'CREATED', 'STATUS_CHANGE', 'PLAN_SELECTED', 'EXECUTION_STARTED',
            'TASK_STARTED', 'TASK_COMPLETED', 'TASK_FAILED',
            'REPLAN_TRIGGERED', 'REPLAN_APPLIED', 'FINALIZED',
            name='missioneventtype', native_enum=False
        ), nullable=False),
        sa.Column('payload', JSONType(), nullable=True),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_mission_events_mission_id', 'mission_events', ['mission_id'])
    op.create_index('ix_mission_events_task_id', 'mission_events', ['task_id'])
    op.create_index('ix_mission_events_event_type', 'mission_events', ['event_type'])

    # ------------------------------------------------------------------
    # 8) task_dependencies (جدول العلاقات الاختياري)
    # ------------------------------------------------------------------
    op.create_table(
        'task_dependencies',
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('depends_on_task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    )

    # ------------------------------------------------------------------
    # END UPGRADE
    # ------------------------------------------------------------------


def downgrade():
    """
    عكس العمليات: أسقط الجداول بترتيب يحترم العلاقات.
    """
    # Drop dependency table
    op.drop_table('task_dependencies')

    # mission_events
    op.drop_index('ix_mission_events_event_type', table_name='mission_events')
    op.drop_index('ix_mission_events_task_id', table_name='mission_events')
    op.drop_index('ix_mission_events_mission_id', table_name='mission_events')
    op.drop_table('mission_events')

    # tasks
    op.drop_index('ix_tasks_tool_name', table_name='tasks')
    op.drop_index('ix_tasks_task_type', table_name='tasks')
    op.drop_index('ix_tasks_task_key', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_plan_id', table_name='tasks')
    op.drop_index('ix_tasks_mission_id', table_name='tasks')
    op.drop_index('ix_task_plan_taskkey', table_name='tasks')
    op.drop_index('ix_task_mission_status', table_name='tasks')
    op.drop_table('tasks')

    # submissions
    op.drop_index('ix_submissions_user_id', table_name='submissions')
    op.drop_index('ix_submissions_exercise_id', table_name='submissions')
    op.drop_table('submissions')

    # Remove FK (missions.active_plan_id) before dropping mission_plans
    with op.batch_alter_table('missions') as batch_op:
        try:
            batch_op.drop_constraint('fk_missions_active_plan_id', type_='foreignkey')
        except Exception:
            # If autogenerate named it differently, ignore silently
            pass

    # mission_plans
    op.drop_index('ix_mission_plans_content_hash', table_name='mission_plans')
    op.drop_index('ix_mission_plans_status', table_name='mission_plans')
    op.drop_index('ix_mission_plans_mission_id', table_name='mission_plans')
    op.drop_table('mission_plans')

    # missions
    op.drop_index('ix_missions_status', table_name='missions')
    op.drop_index('ix_missions_initiator_id', table_name='missions')
    op.drop_table('missions')

    # exercises
    op.drop_index('ix_exercises_lesson_id', table_name='exercises')
    op.drop_table('exercises')

    # lessons
    op.drop_index('ix_lessons_subject_id', table_name='lessons')
    op.drop_table('lessons')

    # users
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    # subjects
    op.drop_index('ix_subjects_name', table_name='subjects')
    op.drop_table('subjects')

    # Drop ENUM types created with native_enum=False? (No actual DB enum types created in this mode)
    # If you later switch native_enum=True, add explicit `op.execute("DROP TYPE ...")` here.
