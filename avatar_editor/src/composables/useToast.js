import { ref } from 'vue'

let toastId = 0
const toasts = ref([])

export function useToast() {
  const DEFAULT_DURATION = 3500

  const remove = (id) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  const add = (message, type = 'info', duration = DEFAULT_DURATION) => {
    const id = ++toastId
    toasts.value.push({ id, message, type, duration })
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }
    return id
  }

  const success = (message, duration) => add(message, 'success', duration)
  const error = (message, duration) => add(message, 'error', duration)
  const info = (message, duration) => add(message, 'info', duration)
  const warning = (message, duration) => add(message, 'warning', duration)

  return { toasts, add, remove, success, error, info, warning }
}