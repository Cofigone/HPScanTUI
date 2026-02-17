<template>
  <div :class="['notification', `status-${type}`]">
    <span class="notification-message">{{ message }}</span>
    <button class="notification-close" @click="$emit('close')">&times;</button>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'info',
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value)
  }
})

defineEmits(['close'])
</script>

<style scoped>
.notification {
  position: fixed;
  top: 70px;
  right: 20px;
  padding: var(--spacing-md) var(--spacing-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  z-index: 1000;
  max-width: 400px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.notification-message {
  flex: 1;
}

.notification-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.7;
  line-height: 1;
}

.notification-close:hover {
  opacity: 1;
}
</style>
