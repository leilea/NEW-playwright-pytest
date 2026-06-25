<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  DataBoard, Collection, VideoPlay,
  DataAnalysis, Clock, Setting, Fold, Expand
} from '@element-plus/icons-vue'

const route = useRoute()
const auth = useAuthStore()
const ui = useUiStore()

const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: DataBoard },
  { path: '/suites', title: '用例仓库', icon: Collection },
  { path: '/runs', title: '用例执行', icon: VideoPlay },
  { path: '/reports', title: '报告', icon: DataAnalysis },
  { path: '/schedules', title: '计划', icon: Clock },
  { path: '/config', title: '配置', icon: Setting },
]
</script>

<template>
  <el-container class="app-layout">
    <el-aside :width="ui.sidebarCollapsed ? '64px' : '220px'" class="app-aside">
      <el-menu
        :default-active="route.path"
        router
        :collapse="ui.sidebarCollapsed"
        class="sidebar-menu"
      >
        <div class="brand-area">
          <span v-if="!ui.sidebarCollapsed">DSEP Test Platform</span>
          <span v-else>DSEP</span>
        </div>
        <el-menu-item v-for="m in menuItems" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <el-button text @click="ui.toggleSidebar">
          <el-icon :size="18"><component :is="ui.sidebarCollapsed ? Expand : Fold" /></el-icon>
        </el-button>
        <div class="header-right">
          <span class="user-name">{{ auth.user?.display_name || auth.user?.email }}</span>
          <el-button text type="danger" @click="auth.logout">退出</el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
}

.app-aside {
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-menu {
  height: 100%;
  border-right: 1px solid var(--el-border-color-light);
}

.brand-area {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 16px;
  color: #ffffff;
  background: var(--el-color-primary);
  letter-spacing: 0.5px;
}

.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  color: var(--el-text-color-regular);
}

.sidebar-menu .el-menu-item {
  font-size: 18px;
}

.sidebar-menu .el-menu-item.is-active {
  background: transparent;
  color: var(--el-color-primary);
  font-weight: 600;
  border-left: 3px solid var(--el-color-primary);
  padding-left: 17px;
}

.sidebar-menu .el-menu-item .el-icon {
  font-size: 18px;
  width: 18px;
  height: 18px;
}

.app-main {
  padding: 24px;
}
</style>
