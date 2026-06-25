"""OD 矩阵计算路由"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import ODMatrixTask
from app.schemas import ODMatrixRequest, ODMatrixTaskResponse, ODMatrixResultResponse
from app.tasks.od_tasks import compute_od_matrix

router = APIRouter(prefix='/api/od-matrix', tags=['OD 矩阵'])


@router.post('/', response_model=ODMatrixTaskResponse)
async def create_od_matrix_task(req: ODMatrixRequest):
    """提交异步 OD 矩阵计算任务"""
    origins = [[o[0], o[1]] for o in req.origins]
    destinations = [[d[0], d[1]] for d in req.destinations]
    task = compute_od_matrix.delay(origins, destinations)
    return ODMatrixTaskResponse(task_id=task.id, status='pending')


@router.get('/{task_id}', response_model=ODMatrixResultResponse)
async def get_od_matrix_result(task_id: str, db: AsyncSession = Depends(get_db)):
    """查询 OD 矩阵计算结果"""
    result = await db.execute(
        select(ODMatrixTask).where(ODMatrixTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        from app.tasks.od_tasks import AsyncResult
        ar = AsyncResult(task_id)
        status = ar.status or 'unknown'
        if status == 'SUCCESS':
            import json
            matrix = ar.result
            return ODMatrixResultResponse(
                task_id=task_id, status='completed', matrix=json.loads(matrix) if isinstance(matrix, str) else matrix
            )
        return ODMatrixResultResponse(task_id=task_id, status=status.lower())

    import json
    matrix = json.loads(task.result) if task.result else None
    return ODMatrixResultResponse(
        task_id=task.task_id,
        status=task.status,
        matrix=matrix,
        created_at=task.created_at,
        updated_at=task.updated_at
    )
