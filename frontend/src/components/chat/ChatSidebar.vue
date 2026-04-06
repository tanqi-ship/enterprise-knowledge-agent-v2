 <template>
  <div class="sidebar-inner">
    <!-- 顶部：新建会话 + 折叠 -->
    <div class="sidebar-header">
      <button class="new-chat-btn" @click="handleNewChat">
        <el-icon><EditPen /></el-icon>
        <span>新对话</span>
      </button>
      <button class="icon-btn" @click="$emit('toggle')" title="收起侧边栏">
        <el-icon><Fold /></el-icon>
      </button>
    </div>

    <!-- 搜索框 -->
    <div class="sidebar-search">
      <el-input
        v-model="searchText"
        placeholder="搜索对话..."
        :prefix-icon="Search"
        clearable
        size="small"
      />
    </div>

    <!-- 会话列表 -->
    <div class="conv-list" v-loading="chatStore.loadingConvs">
      <template v-if="filteredConvs.length > 0">
        <ConvItem
          v-for="conv in filteredConvs"
          :key="conv.thread_id"
          :conv="conv"
          :active="conv.thread_id === chatStore.currentConvId"
          @select="handleSelect(conv.thread_id)"
          @rename="handleRename(conv)"
          @delete="handleDelete(conv.thread_id)"
        />
      </template>
      <div v-else class="conv-empty">
        <el-icon :size="32" color="#c0c4cc"><ChatDotRound /></el-icon>
        <p>暂无对话</p>
      </div>
    </div>

    <!-- 底部用户信息 -->
    <div class="sidebar-footer">
      <div class="user-info">
        <el-avatar :size="32" :style="avatarStyle">
          {{ avatarText }}
        </el-avatar>
        <div class="user-meta">
          <span class="user-name">{{ userStore.username || '用户' }}</span>
          <el-tag v-if="userStore.isAdmin" size="small" type="danger">
            管理员
          </el-tag>
        </div>
      </div>
      <el-dropdown trigger="click" @command="handleCommand">
        <button class="icon-btn">
          <el-icon><MoreFilled /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <!-- ✅ 管理员才显示 -->
            <template v-if="userStore.isAdmin">
              <el-dropdown-item command="vectordb" :icon="DataBoard">
                向量数据库管理
              </el-dropdown-item>
              <el-dropdown-item command="userManage" :icon="UserFilled">
                用户管理
              </el-dropdown-item>
            </template>



            <el-dropdown-item command="logout" :icon="SwitchButton" divided>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- 重命名对话框 -->
    <el-dialog
      v-model="renameDialog.visible"
      title="重命名对话"
      width="360px"
      :close-on-click-modal="false"
      align-center
    >
      <el-input
        v-model="renameDialog.title"
        placeholder="请输入对话名称"
        maxlength="30"
        show-word-limit
        @keyup.enter="confirmRename"
      />
      <template #footer>
        <el-button @click="renameDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="confirmRename">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  EditPen, Fold, Search, ChatDotRound,
  MoreFilled, SwitchButton, DataBoard,
  UserFilled, MagicStick               // ✅ 修正拼写
} from '@element-plus/icons-vue'
import { useChatStore } from '@/store/chat.js'
import { useUserStore } from '@/store/user.js'
import ConvItem from './ConvItem.vue'
import { updateUserRoleAPI } from '@/api/user.js'  // ✅ 新增

defineEmits(['toggle'])

const router = useRouter()
const chatStore = useChatStore()
const userStore = useUserStore()

// ✅ 判断是否为开发环境
const isDev = import.meta.env.DEV

// ── 搜索 ──────────────────────────────────────────────────
const searchText = ref('')
const filteredConvs = computed(() => {
  const q = searchText.value.trim().toLowerCase()
  if (!q) return chatStore.sortedConversations
  return chatStore.sortedConversations.filter((c) =>
    c.title.toLowerCase().includes(q)
  )
})

// ── 头像 ──────────────────────────────────────────────────
const avatarText = computed(() => {
  const name = userStore.username || '用'
  return name.charAt(0).toUpperCase()
})
const avatarStyle = computed(() => ({
  background: 'var(--color-primary)',
  color: '#fff',
  fontSize: '14px',
  fontWeight: 600,
  flexShrink: 0
}))

// ── 新建会话 ──────────────────────────────────────────────
const handleNewChat = async () => {
  try {
    await chatStore.createConversation()
  } catch (err) {
    ElMessage.error(err.message || '创建失败')
  }
}

// ── 选择会话 ──────────────────────────────────────────────
const handleSelect = async (id) => {
  try {
    await chatStore.selectConversation(id)
  } catch (err) {
    ElMessage.error('加载消息失败')
  }
}

// ── 重命名 ────────────────────────────────────────────────
const renameDialog = reactive({ visible: false, id: null, title: '' })

const handleRename = (conv) => {
  renameDialog.id = conv.thread_id
  renameDialog.title = conv.title
  renameDialog.visible = true
}

const confirmRename = async () => {
  const title = renameDialog.title.trim()
  if (!title) return ElMessage.warning('名称不能为空')
  try {
    await chatStore.renameConversation(renameDialog.id, title)
    renameDialog.visible = false
    ElMessage.success('重命名成功')
  } catch (err) {
    ElMessage.error(err.message || '重命名失败')
  }
}

// ── 删除 ──────────────────────────────────────────────────
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除此对话？删除后不可恢复', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    })
    await chatStore.deleteConversation(id)
    ElMessage.success('已删除')
  } catch {
    // 用户取消，忽略
  }
}

// ── 底部菜单 ──────────────────────────────────────────────
const handleCommand = async (cmd) => {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定退出登录？', '提示', {
        confirmButtonText: '退出',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await userStore.logout()
      router.push('/login')
    } catch { }

  } else if (cmd === 'vectordb') {
    router.push('/vector-db')

  } else if (cmd === 'userManage') {
    router.push('/admin/users')

  } else if (cmd === 'devSetAdmin') {
    // ✅ 开发环境快速提升角色，不需要手动改数据库
    try {
      await updateUserRoleAPI(userStore.userInfo.id, 'admin')
      await userStore.fetchUserInfo()   // 重新拉取用户信息
      ElMessage.success('已提升为管理员，刷新生效')
    } catch (err) {
      ElMessage.error(err.message || '操作失败，请手动修改数据库')
    }
  }
}
</script>

<style scoped>
.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  width: var(--sidebar-width);
}

/* 顶部 */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--color-border);
}
.new-chat-btn {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-primary-light);
  color: var(--color-primary);
  border: 1px solid #d9ecff;
  border-radius: var(--radius-base);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.new-chat-btn:hover {
  background: #d9ecff;
}
.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}
.icon-btn:hover {
  background: var(--color-bg);
  color: var(--color-text-primary);
}

/* 搜索 */
.sidebar-search {
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border);
}

/* 会话列表 */
.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}
.conv-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

/* 底部用户信息 */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-top: 1px solid var(--color-border);
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}
</style>
