<template>
  <div
    class="conv-item"
    :class="{ active }"
    @click="$emit('select')"
  >
    <el-icon class="conv-icon"><ChatDotRound /></el-icon>

    <!-- 标题 -->
    <span class="conv-title">{{ conv.title || '新对话' }}</span>

    <!-- 操作按钮（hover时显示） -->
    <div class="conv-actions" @click.stop>
      <button
        class="action-btn"
        title="重命名"
        @click="$emit('rename')"
      >
        <el-icon><EditPen /></el-icon>
      </button>
      <button
        class="action-btn danger"
        title="删除"
        @click="$emit('delete')"
      >
        <el-icon><Delete /></el-icon>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound, EditPen, Delete } from '@element-plus/icons-vue'

defineProps({
  conv: { type: Object, required: true },
  active: { type: Boolean, default: false }
})

defineEmits(['select', 'rename', 'delete'])
</script>

<style scoped>
.conv-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-base);
  cursor: pointer;
  transition: background 0.15s;
  position: relative;
  min-height: 38px;
}
.conv-item:hover {
  background: var(--color-bg);
}
.conv-item.active {
  background: var(--color-primary-light);
}
.conv-icon {
  color: var(--color-text-secondary);
  flex-shrink: 0;
  font-size: 15px;
}
.conv-item.active .conv-icon {
  color: var(--color-primary);
}
.conv-title {
  flex: 1;
  font-size: 13px;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.conv-item.active .conv-title {
  color: var(--color-primary);
  font-weight: 500;
}

/* 操作按钮，默认隐藏 */
.conv-actions {
  display: none;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.conv-item:hover .conv-actions,
.conv-item.active .conv-actions {
  display: flex;
}
.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: none;
  background: transparent;
  border-radius: 4px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-size: 13px;
}
.action-btn:hover {
  background: rgba(0, 0, 0, 0.06);
  color: var(--color-text-primary);
}
.action-btn.danger:hover {
  background: #fff0f0;
  color: #f56c6c;
}
</style>
