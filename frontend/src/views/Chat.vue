<template>
  <div class="chat-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <ChatSidebar
        :collapsed="sidebarCollapsed"
        @toggle="sidebarCollapsed = !sidebarCollapsed"
      />
    </aside>

    <!-- 主区域：把 collapsed 状态传下去 -->
    <main class="chat-main">
      <ChatWindow
        :sidebar-collapsed="sidebarCollapsed"
        @expand-sidebar="sidebarCollapsed = false"
      />
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/store/chat.js'
import { useUserStore } from '@/store/user.js'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import ChatWindow from '@/components/chat/ChatWindow.vue'

const chatStore = useChatStore()
const userStore = useUserStore()
const sidebarCollapsed = ref(false)

onMounted(async () => {
  // 加载会话列表
  await chatStore.fetchConversations()

  // 恢复上次会话 或 自动选中最新的
  if (chatStore.currentConvId) {
    const exists = chatStore.conversations.find(
      (c) => c.thread_id === chatStore.currentConvId
    )
    if (exists) {
      await chatStore.fetchMessages(chatStore.currentConvId)
    } else {
      chatStore.currentConvId = null
    }
  }

  // 没有会话时自动创建一个
  if (!chatStore.currentConvId && chatStore.conversations.length === 0) {
    await chatStore.createConversation()
  } else if (!chatStore.currentConvId && chatStore.conversations.length > 0) {
    await chatStore.selectConversation(chatStore.sortedConversations[0].thread_id)
  }
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}

/* 侧边栏 */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  transition: width 0.25s ease;
  overflow: hidden;
}
.sidebar.collapsed {
  width: 0;
}

/* 主区域 */
.chat-main {
  flex: 1;
  min-width: 0; /* 防止 flex 子元素溢出 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
