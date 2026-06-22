import * as React from "react"

type ToastActionElement = React.ReactElement
type ToastProps = { id: string; title?: string; description?: string; action?: ToastActionElement; variant?: "default" | "destructive" }

const TOAST_LIMIT = 3
const TOAST_REMOVE_DELAY = 3000

let count = 0
function genId() { return (++count).toString() }

type State = { toasts: ToastProps[] }
let memoryState: State = { toasts: [] }
const listeners: Array<(s: State) => void> = []

function dispatch(toasts: ToastProps[]) {
  memoryState = { toasts }
  listeners.forEach((l) => l(memoryState))
}

export function toast(props: Omit<ToastProps, "id">) {
  const id = genId()
  const newToast = { ...props, id }
  const updated = [newToast, ...memoryState.toasts].slice(0, TOAST_LIMIT)
  dispatch(updated)
  setTimeout(() => dispatch(memoryState.toasts.filter((t) => t.id !== id)), TOAST_REMOVE_DELAY)
  return id
}

export function useToast() {
  const [state, setState] = React.useState<State>(memoryState)
  React.useEffect(() => {
    listeners.push(setState)
    return () => { const i = listeners.indexOf(setState); if (i > -1) listeners.splice(i, 1) }
  }, [])
  return { toasts: state.toasts, toast, dismiss: (id: string) => dispatch(state.toasts.filter((t) => t.id !== id)) }
}
