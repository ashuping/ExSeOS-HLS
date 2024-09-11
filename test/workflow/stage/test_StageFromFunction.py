
from modules.data.Variable import BoundVariable, UnboundVariable
from modules.workflow.stage.StageFromFunction import StageFromFunction, make_StageFromFunction
from modules.types.Option import Some

def test_basic_function():
	def fn(x: int) -> int:
		print('calling inner function')
		return 2*x

	stage = make_StageFromFunction(fn)(
		UnboundVariable('x')
	)
		
	res = stage.run(
		(BoundVariable('x', 2),)
	)

	assert len(res.outputs) == 1
	assert res.outputs[0].val == 4

def test_input_types():
	def fn(x: int, y: str, z = 'test') -> bool:
		return True

	stage_cls = make_StageFromFunction(fn)

	print(f'input_vars: {stage_cls.input_vars}')

	[print(var) for var in stage_cls.input_vars]

	assert stage_cls.input_vars == (
		UnboundVariable('x', Some(int)),
		UnboundVariable('y', Some(str)),
		UnboundVariable('z', default=Some('test'))
	)

	assert stage_cls.output_vars == (UnboundVariable('return', Some(bool)),)

def test_side_effecting_function():
	global fn_run_count
	fn_run_count = 0
	def fn():
		global fn_run_count
		fn_run_count += 1


	stage_cls = make_StageFromFunction(fn)

	assert stage_cls.input_vars == ()
	assert stage_cls.output_vars == ()

	assert len(stage_cls().run(()).outputs) == 0
	assert fn_run_count == 1