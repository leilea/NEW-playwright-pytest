export type StepAction = 'goto' | 'click' | 'fill' | 'expect' | 'check' | 'select' | 'hover' | 'wait' | 'screenshot' | 'scroll' | 'eval'
export interface Step {
  action: StepAction
  selector?: string
  value?: string
  expect?: string
  timeout_ms?: number
  note?: string
}
export const STEP_ACTIONS: StepAction[] = ['goto','click','fill','expect','check','select','hover','wait','screenshot','scroll','eval']
