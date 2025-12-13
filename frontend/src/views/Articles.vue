<template>
  <Layout>
    <div class="articles-page">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ sortedArticles.length }}</div>
              <div class="stat-label">总文章数</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon today">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ todayCount }}</div>
              <div class="stat-label">今日文章</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon category">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ categories.length }}</div>
              <div class="stat-label">分类数量</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 筛选栏 -->
      <el-card class="filter-card">
        <div class="filter-header">
          <div class="filter-title">
            <el-icon><Filter /></el-icon>
            <span>筛选条件</span>
          </div>
          <el-button size="small" type="primary" :icon="Refresh" @click="fetchArticles" :loading="loading.articles">
            刷新
          </el-button>
        </div>
        <div class="filter-content">
          <div class="filter-row">
            <div class="filter-item">
              <label>搜索标题</label>
              <el-input
                v-model="articleQuery"
                size="default"
                placeholder="输入关键词搜索..."
                clearable
                @keydown.enter="fetchArticles"
                @clear="fetchArticles"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            <div class="filter-item">
              <label>分类筛选</label>
              <el-select
                v-model="selectedCategory"
                size="default"
                placeholder="全部分类"
                clearable
                @change="fetchArticles"
                style="width: 180px"
              >
                <el-option label="全部" value="" />
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>时间范围</label>
              <el-switch
                v-model="todayOnly"
                active-text="仅今日"
                inactive-text="全部"
                @change="fetchArticles"
              />
            </div>
            <div class="filter-item">
              <label>排序方式</label>
              <el-select v-model="articleSort" size="default" style="width: 140px" @change="fetchArticles">
                <el-option label="时间倒序" value="desc" />
                <el-option label="时间正序" value="asc" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>视图模式</label>
              <el-radio-group v-model="articleView" size="default" @change="onArticleViewChange">
                <el-radio-button label="list">
                  <el-icon><List /></el-icon>
                  <span>列表</span>
                </el-radio-button>
                <el-radio-button label="mp">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>汇总</span>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 文章列表 -->
      <el-card class="content-card">
        <template v-if="articleView === 'list'">
          <div v-if="articlesPaged.length === 0" class="empty-state">
            <el-icon class="empty-icon"><DocumentDelete /></el-icon>
            <p>暂无文章数据</p>
          </div>
          <div v-else class="articles-grid">
            <div
              v-for="article in articlesPaged"
              :key="article.id"
              class="article-card"
              @click="openArticle(article.url)"
            >
              <div class="article-header">
                <div class="article-mp">
                  <el-icon><User /></el-icon>
                  <span>{{ article.mp_name || "未知" }}</span>
                </div>
                <div class="article-time">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatTime(article.publish_at) }}</span>
                </div>
              </div>
              <div class="article-title">{{ article.title }}</div>
              <div class="article-footer">
                <el-button size="small" type="primary" link @click.stop="openArticle(article.url)">
                  <el-icon><Link /></el-icon>
                  阅读全文
                </el-button>
              </div>
            </div>
          </div>
          <div class="pager-wrapper">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :page-size="articlesPageSize"
              :page-sizes="[20, 50, 100]"
              :total="sortedArticles.length"
              :current-page="articlesPage"
              @size-change="handleArticleSizeChange"
              @current-change="handleArticleCurrentChange"
            />
          </div>
        </template>

        <!-- 公众号汇总视图 -->
        <template v-else>
          <div class="mp-summary-grid">
            <el-card
              v-for="mp in mpSummary"
              :key="mp.mp_name"
              class="mp-card"
              shadow="hover"
            >
              <div class="mp-card-content">
                <div class="mp-avatar">
                  <el-icon><UserFilled /></el-icon>
                </div>
                <div class="mp-info">
                  <div class="mp-name">{{ mp.mp_name }}</div>
                  <div class="mp-stats">
                    <span class="mp-count">{{ mp.count }} 篇文章</span>
                    <span class="mp-time">最新：{{ formatTime(mp.latest) }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </template>
      </el-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage } from "element-plus";
import {
  Document,
  Calendar,
  Collection,
  Filter,
  Refresh,
  Search,
  List,
  DataAnalysis,
  DocumentDelete,
  User,
  Clock,
  Link,
  UserFilled,
} from "@element-plus/icons-vue";
import Layout from "./Layout.vue";

const articles = ref([]);
const categories = ref([]);
const loading = ref({ articles: false });
const articleQuery = ref("");
const selectedCategory = ref("");
const todayOnly = ref(false);
const articleView = ref("list");
const articleSort = ref("desc");
const articlesPage = ref(1);
const articlesPageSize = ref(20);

const formatTime = (val) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "");

const fetchCategories = async () => {
  try {
    const { data } = await http.get("/targets/categories");
    categories.value = data || [];
  } catch {
    // 忽略错误，分类是可选的
  }
};

const fetchArticles = async () => {
  loading.value.articles = true;
  try {
    const params = { page: 1, page_size: 200, q: articleQuery.value };
    if (selectedCategory.value) {
      params.category = selectedCategory.value;
    }
    if (todayOnly.value) {
      const start = dayjs().startOf("day").toISOString();
      const end = dayjs().endOf("day").toISOString();
      params.start = start;
      params.end = end;
    }
    const { data } = await http.get("/articles", { params });
    articles.value = data.items || [];
  } catch {
    ElMessage.error("获取文章失败");
  } finally {
    loading.value.articles = false;
  }
};

const sortedArticles = computed(() => {
  const arr = [...(articles.value || [])];
  return arr.sort((a, b) => {
    const ta = new Date(a.publish_at || a.created_at || 0).getTime();
    const tb = new Date(b.publish_at || b.created_at || 0).getTime();
    return articleSort.value === "asc" ? ta - tb : tb - ta;
  });
});

const todayCount = computed(() => {
  const today = dayjs().startOf("day");
  return sortedArticles.value.filter((article) => {
    const publishTime = dayjs(article.publish_at);
    return publishTime.isSame(today, "day");
  }).length;
});

const articlesPaged = computed(() => {
  const start = (articlesPage.value - 1) * articlesPageSize.value;
  return sortedArticles.value.slice(start, start + articlesPageSize.value);
});

const mpSummary = computed(() => {
  const map = new Map();
  sortedArticles.value.forEach((item) => {
    const key = item.mp_name || "未知";
    const ts = new Date(item.publish_at || item.created_at || 0).getTime();
    if (!map.has(key)) {
      map.set(key, { mp_name: key, count: 0, latest: 0 });
    }
    const obj = map.get(key);
    obj.count += 1;
    obj.latest = Math.max(obj.latest, ts);
  });
  return Array.from(map.values()).sort((a, b) => b.count - a.count);
});

const onArticleViewChange = () => {
  // no-op for now
};

const openArticle = (url) => {
  if (url) {
    window.open(url, "_blank");
  }
};

const handleArticleSizeChange = (val) => {
  articlesPageSize.value = val;
  articlesPage.value = 1;
};

const handleArticleCurrentChange = (val) => {
  articlesPage.value = val;
};

onMounted(() => {
  fetchCategories();
  fetchArticles();
});
</script>

<style scoped>
.articles-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 8px;
}

.stat-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.today {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.category {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

/* 筛选卡片 */
.filter-card {
  border-radius: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #1f2d3d;
}

.filter-content {
  padding: 8px 0;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 160px;
}

.filter-item label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

/* 内容卡片 */
.content-card {
  border-radius: 12px;
  min-height: 400px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
}

/* 文章网格 */
.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 8px 0;
}

.article-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #909399;
}

.article-mp,
.article-time {
  display: flex;
  align-items: center;
  gap: 6px;
}

.article-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.article-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid #f5f7fa;
}

/* 公众号汇总网格 */
.mp-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.mp-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.mp-card:hover {
  transform: translateY(-2px);
}

.mp-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mp-avatar {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  flex-shrink: 0;
}

.mp-info {
  flex: 1;
  min-width: 0;
}

.mp-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mp-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.mp-count {
  font-weight: 500;
  color: #409eff;
}

/* 分页 */
.pager-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }

  .articles-grid {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-item {
    width: 100%;
  }
}
</style>
