"""empty message

Revision ID: 593366be4eff
Revises: 583d4c1d254f
Create Date: 2026-02-06 11:29:58.380567

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '593366be4eff'
down_revision = '583d4c1d254f'
branch_labels = None
depends_on = None


def upgrade():


    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=500),
               comment='英文名',
               existing_nullable=False)
        batch_op.alter_column('describe',
               existing_type=mysql.TEXT(),
               type_=sa.String(length=1000),
               comment='描述',
               existing_nullable=False)

    with op.batch_alter_table('inferenceservice', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=2000),
               comment='挂载',
               existing_nullable=True)

    with op.batch_alter_table('job_template', schema=None) as batch_op:
        batch_op.alter_column(
            'hostAliases',
            new_column_name='host_aliases',
            existing_type=sa.Text(),
            existing_nullable=True,
            existing_comment='域名映射'
        )


        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=500),
               comment='英文名',
               existing_nullable=False)
        batch_op.alter_column('describe',
               existing_type=mysql.TEXT(),
               type_=sa.String(length=500),
               comment='描述',
               existing_nullable=False)
        batch_op.alter_column('volume_mount',
               existing_type=mysql.VARCHAR(length=400),
               type_=sa.String(length=2000),
               comment='强制必须挂载',
               existing_nullable=True)


    with op.batch_alter_table('nni', schema=None) as batch_op:
        batch_op.alter_column(
            'maxExecDuration',
            new_column_name='max_exec_duration',
            existing_type=sa.Integer(),
            existing_nullable=True,
            existing_comment='最大执行时长'
        )

    with op.batch_alter_table('notebook', schema=None) as batch_op:
        batch_op.alter_column('describe',
               existing_type=mysql.TEXT(),
               type_=sa.String(length=200),
               comment='描述',
               existing_nullable=True)
        batch_op.alter_column('images',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=1000),
               comment='镜像',
               existing_nullable=True)
        batch_op.alter_column('ide_type',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=100),
               comment='ide类型',
               existing_nullable=True)

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('describe',
               existing_type=mysql.TEXT(),
               type_=sa.String(length=500),
               comment='描述',
               existing_nullable=False)

    with op.batch_alter_table('project_user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('org', sa.String(length=200), nullable=True, comment='用户成员可用资源组'))
        batch_op.add_column(sa.Column('expand', sa.Text(length=65536), nullable=True, comment='扩展参数'))

    with op.batch_alter_table('repository', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.String(length=200),
               comment='英文名',
               existing_nullable=False)
        batch_op.alter_column('server',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=200),
               comment='仓库地址',
               existing_nullable=False)
    with op.batch_alter_table('run', schema=None) as batch_op:
        batch_op.alter_column('execution_date',
               existing_type=mysql.VARCHAR(length=100),
               type_=sa.String(length=200),
               comment='执行时间',
               existing_nullable=False)
    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=2000),
               comment='挂载',
               existing_nullable=True)

    with op.batch_alter_table('sqlab_query', schema=None) as batch_op:
        batch_op.alter_column('err_msg',
               existing_type=mysql.VARCHAR(length=5000),
               type_=sa.Text(),
               comment='报错消息',
               existing_nullable=True)

    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=mysql.VARCHAR(length=200),
               type_=sa.String(length=2000),
               comment='挂载',
               existing_nullable=True)

    try:
        with op.batch_alter_table('ab_user', schema=None) as batch_op:
            batch_op.add_column(sa.Column('nickname', sa.String(length=200), nullable=True))
    except Exception as e:
        print(e)


def downgrade():
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=sa.String(length=2000),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='挂载',
               existing_nullable=True)

    with op.batch_alter_table('sqlab_query', schema=None) as batch_op:
        batch_op.alter_column('err_msg',
               existing_type=sa.Text(),
               type_=mysql.VARCHAR(length=5000),
               comment=None,
               existing_comment='报错消息',
               existing_nullable=True)

    with op.batch_alter_table('service', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=sa.String(length=2000),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='挂载',
               existing_nullable=True)

    with op.batch_alter_table('run', schema=None) as batch_op:
        batch_op.alter_column('execution_date',
               existing_type=sa.String(length=200),
               type_=mysql.VARCHAR(length=100),
               comment=None,
               existing_comment='执行时间',
               existing_nullable=False)

    with op.batch_alter_table('repository', schema=None) as batch_op:
        batch_op.alter_column('server',
               existing_type=sa.String(length=200),
               type_=mysql.VARCHAR(length=100),
               comment=None,
               existing_comment='仓库地址',
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=200),
               type_=mysql.VARCHAR(length=50),
               comment=None,
               existing_comment='英文名',
               existing_nullable=False)

    with op.batch_alter_table('project_user', schema=None) as batch_op:
        batch_op.drop_column('expand')
        batch_op.drop_column('org')

    with op.batch_alter_table('project', schema=None) as batch_op:
        batch_op.alter_column('describe',
               existing_type=sa.String(length=500),
               type_=mysql.TEXT(),
               comment=None,
               existing_comment='描述',
               existing_nullable=False)

    with op.batch_alter_table('notebook', schema=None) as batch_op:
        batch_op.alter_column('ide_type',
               existing_type=sa.String(length=100),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='ide类型',
               existing_nullable=True)
        batch_op.alter_column('images',
               existing_type=sa.String(length=1000),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='镜像',
               existing_nullable=True)
        batch_op.alter_column('describe',
               existing_type=sa.String(length=200),
               type_=mysql.TEXT(),
               comment=None,
               existing_comment='描述',
               existing_nullable=True)

    with op.batch_alter_table('nni', schema=None) as batch_op:
        batch_op.alter_column(
            'max_exec_duration',
            new_column_name='maxExecDuration',
            existing_type=mysql.INTEGER(),
            existing_nullable=True,
            existing_autoincrement=False
        )


    with op.batch_alter_table('job_template', schema=None) as batch_op:
        batch_op.alter_column(
            'host_aliases',
            new_column_name='hostAliases',
            existing_type=mysql.TEXT(),
            existing_nullable=True
        )

        batch_op.alter_column('volume_mount',
               existing_type=sa.String(length=2000),
               type_=mysql.VARCHAR(length=400),
               comment=None,
               existing_comment='强制必须挂载',
               existing_nullable=True)
        batch_op.alter_column('describe',
               existing_type=sa.String(length=500),
               type_=mysql.TEXT(),
               comment=None,
               existing_comment='描述',
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=500),
               type_=mysql.VARCHAR(length=100),
               comment=None,
               existing_comment='英文名',
               existing_nullable=False)


    with op.batch_alter_table('inferenceservice', schema=None) as batch_op:
        batch_op.alter_column('volume_mount',
               existing_type=sa.String(length=2000),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='挂载',
               existing_nullable=True)


    with op.batch_alter_table('images', schema=None) as batch_op:
        batch_op.alter_column('describe',
               existing_type=sa.String(length=1000),
               type_=mysql.TEXT(),
               comment=None,
               existing_comment='描述',
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=500),
               type_=mysql.VARCHAR(length=200),
               comment=None,
               existing_comment='英文名',
               existing_nullable=False)
