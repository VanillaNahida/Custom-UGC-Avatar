<script setup>
import { useToast } from '../composables/useToast.js'

const { toasts, remove } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="toast-container" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
          @click="remove(toast.id)"
        >
          <span class="toast-icon">
            <!-- success: checkmark -->
            <svg v-if="toast.type === 'success'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
              <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
              <path d="M6 10.5l2.5 2.5 5.5-5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <!-- error: x mark -->
            <svg v-if="toast.type === 'error'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
              <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
              <path d="M7.5 7.5l5 5m0-5l-5 5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <!-- warning: triangle -->
            <svg v-if="toast.type === 'warning'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
              <path d="M10 3.5l-8 14h16l-8-14z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
              <path d="M10 9v3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              <circle cx="10" cy="14.5" r="1" fill="currentColor"/>
            </svg>
            <!-- info: i circle -->
            <svg v-if="toast.type === 'info'" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" width="20" height="20">
              <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.5"/>
              <path d="M10 9v5.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              <circle cx="10" cy="6.5" r="1" fill="currentColor"/>
            </svg>
          </span>
          <span class="toast-message">{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 2000;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
  pointer-events: none;
  max-width: 380px;
}

.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.4;
  cursor: pointer;
  pointer-events: auto;
  border: 1px solid;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
}

.toast--success {
  background: oklch(0.18 0.03 145);
  border-color: oklch(0.35 0.08 145);
  color: oklch(0.85 0.06 145);
}

.toast--error {
  background: oklch(0.18 0.03 25);
  border-color: oklch(0.35 0.08 25);
  color: oklch(0.85 0.06 25);
}

.toast--warning {
  background: oklch(0.18 0.03 85);
  border-color: oklch(0.35 0.08 85);
  color: oklch(0.85 0.06 85);
}

.toast--info {
  background: var(--bg-card);
  border-color: var(--border);
  color: var(--text-primary);
}

.toast-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast--success .toast-icon {
  color: oklch(0.85 0.06 145);
}

.toast--error .toast-icon {
  color: oklch(0.85 0.06 25);
}

.toast--warning .toast-icon {
  color: oklch(0.85 0.06 85);
}

.toast--info .toast-icon {
  color: var(--text-primary);
}

.toast-message {
  flex: 1;
  word-break: break-word;
}

/* TransitionGroup animations */
.toast-enter-active {
  transition: all 300ms var(--ease-out);
}

.toast-leave-active {
  transition: all 200ms ease-in;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(40px) scale(0.95);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(40px) scale(0.95);
}
</style>