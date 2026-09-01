import Vue from 'vue'
import Router from 'vue-router'

Vue.use(Router)

export default new Router({
  mode: 'history',
  routes: [
    {
      path: '/',
      redirect: '/effekt'
    },
    {
      path: '/Login',
      name: 'login',
      component: (resolve) => require(['@/components/User/Login'], resolve)
    },
    {
      path: '/Register',
      name: 'register',
      component: (resolve) => require(['@/components/User/Register'], resolve)
    },
    {
      path: '/CreateData',
      name: 'home',
      component: (resolve) => require(['@/components/Home'], resolve),
      redirect: '/effekt',
      children:[
        {
          path: '/effekt',
          name: 'EffektHome',
          components: {
            Manage: (resolve) => require(['@/components/EffektHome'], resolve)
          }
        },
        {
          path: '/data-tools/db-builder',
          name: 'CreateManage',
          components: {
            Manage: (resolve) => require(['@/components/CreateData/CreateManage'], resolve)
          }
        },
        {
          path: '/create/info',
          name: 'CreateDataInfo',
          components: {
            Manage: (resolve) => require(['@/components/CreateData/CreateDataInfo'], resolve)
          }
        },
        {
          path: '/create/result/list',
          name: 'CreateResultList',
          components: {
            Manage: (resolve) => require(['@/components/CreateData/CreateResultList'], resolve)
          }
        },
        {
          path: '/create/result',
          name: 'CreateResult',
          components: {
            Manage: (resolve) => require(['@/components/CreateData/CreateResult'], resolve)
          }
        },
        {
          path: '/create/interface',
          name: 'CreateInterfacePlaceholder',
          components: {
            Manage: (resolve) => require(['@/components/EffektHome'], resolve)
          }
        },
        {
          path: '/test-platform/project',
          name: 'ProjectList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Project/ProjectList'], resolve)
          }
        },
        {
          path: '/test-platform/product',
          name: 'ProductList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Product/ProductList'], resolve)
          }
        },
        {
          path: '/test-platform/project/detail',
          name: 'ProjectDetail',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Project/ProjectDetail'], resolve)
          }
        },
        {
          path: '/test-platform/project/setting',
          name: 'ProjectSettings',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Project/ProjectSettings'], resolve)
          }
        },
        {
          path: '/test-platform/skill-rules',
          name: 'BusinessSkillRuleConfig',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/SkillRule/BusinessSkillRuleConfig'], resolve)
          }
        },
        {
          path: '/test-platform/ai-platform',
          name: 'AiPlatform',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/AI/AiPlatform'], resolve)
          }
        },
        {
          path: '/ai-review',
          name: 'AiReviewList',
          components: {
            Manage: (resolve) => require(['@/components/AIReview/ReviewList'], resolve)
          }
        },
        {
          path: '/ai-review/create',
          name: 'AiReviewCreate',
          components: {
            Manage: (resolve) => require(['@/components/AIReview/ReviewCreate'], resolve)
          }
        },
        {
          path: '/ai-review/detail',
          name: 'AiReviewDetail',
          components: {
            Manage: (resolve) => require(['@/components/AIReview/ReviewDetail'], resolve)
          }
        },
        {
          path: '/ai-workload-estimate',
          name: 'AiWorkloadEstimateList',
          components: {
            Manage: (resolve) => require(['@/components/AIWorkloadEstimate/EstimateList'], resolve)
          }
        },
        {
          path: '/ai-workload-estimate/create',
          name: 'AiWorkloadEstimateCreate',
          components: {
            Manage: (resolve) => require(['@/components/AIWorkloadEstimate/EstimateCreate'], resolve)
          }
        },
        {
          path: '/ai-workload-estimate/detail',
          name: 'AiWorkloadEstimateDetail',
          components: {
            Manage: (resolve) => require(['@/components/AIWorkloadEstimate/EstimateDetail'], resolve)
          }
        },
        {
          path: '/test-asset-governance',
          name: 'TestAssetGovernanceScanList',
          components: {
            Manage: (resolve) => require(['@/components/TestAssetGovernance/ScanList'], resolve)
          }
        },
        {
          path: '/test-asset-governance/detail',
          name: 'TestAssetGovernanceScanDetail',
          components: {
            Manage: (resolve) => require(['@/components/TestAssetGovernance/ScanDetail'], resolve)
          }
        },
        {
          path: '/test-platform/case',
          name: 'CaseList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Case/CaseList'], resolve)
          }
        },
        {
          path: '/test-platform/case/editor',
          name: 'CaseEditor',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Case/CaseEditor'], resolve)
          }
        },
        {
          path: '/test-platform/case/review',
          name: 'CaseReview',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Case/CaseReview'], resolve)
          }
        },
        {
          path: '/test-platform/plan',
          name: 'PlanList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanList'], resolve)
          }
        },
        {
          path: '/test-platform/plan/builder',
          name: 'PlanBuilder',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanBuilder'], resolve)
          }
        },
        {
          path: '/test-platform/plan/execute',
          name: 'PlanExecute',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanExecute'], resolve)
          }
        },
        {
          path: '/test-platform/plan/automation',
          name: 'PlanAutomationRun',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanAutomationRun'], resolve)
          }
        },
        {
          path: '/test-platform/plan/automation/executions',
          name: 'PlanAutomationExecutionList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanAutomationExecutionList'], resolve)
          }
        },
        {
          path: '/test-platform/plan/progress',
          name: 'PlanProgress',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanProgress'], resolve)
          }
        },
        {
          path: '/test-platform/plan/case/add',
          name: 'PlanCaseAdd',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Plan/PlanCaseAdd'], resolve)
          }
        },
        {
          path: '/test-platform/report',
          name: 'ReportList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Report/ReportList'], resolve)
          }
        },
        {
          path: '/test-platform/report/viewer',
          name: 'ReportViewer',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/Report/ReportViewer'], resolve)
          }
        },
        {
          path: '/performance',
          redirect: '/performance/scenarios'
        },
        {
          path: '/performance/scenarios',
          name: 'PerformanceScenarioList',
          components: {
            Manage: (resolve) => require(['@/components/Performance/ScenarioList'], resolve)
          }
        },
        {
          path: '/performance/run-wizard',
          name: 'PerformanceRunWizard',
          components: {
            Manage: (resolve) => require(['@/components/Performance/RunWizard'], resolve)
          }
        },
        {
          path: '/performance/runs',
          name: 'PerformanceRunList',
          components: {
            Manage: (resolve) => require(['@/components/Performance/RunList'], resolve)
          }
        },
        {
          path: '/performance/reports',
          name: 'PerformanceReportList',
          components: {
            Manage: (resolve) => require(['@/components/Performance/ReportList'], resolve)
          }
        },
        {
          path: '/performance/machines',
          name: 'PerformanceMachinePool',
          components: {
            Manage: (resolve) => require(['@/components/Performance/MachinePool'], resolve)
          }
        },
        {
          path: '/mobile-automation',
          redirect: '/mobile-automation/devices'
        },
        {
          path: '/mobile-automation/devices',
          name: 'MobileAutomationDevices',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/EnvironmentCheck'], resolve)
          }
        },
        {
          path: '/mobile-automation/apps',
          name: 'MobileAutomationApps',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/AppList'], resolve)
          }
        },
        {
          path: '/mobile-automation/run',
          name: 'MobileAutomationRun',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/ExecutionList'], resolve)
          }
        },
        {
          path: '/mobile-automation/run/edit',
          name: 'MobileAutomationRunEdit',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/ExecutionCreate'], resolve)
          }
        },
        {
          path: '/mobile-automation/executions',
          name: 'MobileAutomationExecutions',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/ExecutionRecordList'], resolve)
          }
        },
        {
          path: '/mobile-automation/execution/detail',
          name: 'MobileAutomationExecutionDetail',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/ExecutionDetail'], resolve)
          }
        },
        {
          path: '/mobile-automation/page-replay',
          name: 'MobileAutomationPageReplay',
          components: {
            Manage: (resolve) => require(['@/components/MobileAutomation/PageReplay'], resolve)
          }
        },
        {
          path: '/inspection',
          redirect: '/inspection/dashboard'
        },
        {
          path: '/inspection/dashboard',
          name: 'InspectionDashboard',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/Dashboard'], resolve)
          }
        },
        {
          path: '/inspection/groups',
          redirect: '/inspection/tasks'
        },
        {
          path: '/inspection/tasks',
          name: 'InspectionTasks',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/TaskWorkspace'], resolve)
          }
        },
        {
          path: '/inspection/task/edit',
          name: 'InspectionTaskEdit',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/TaskForm'], resolve)
          }
        },
        {
          path: '/inspection/db-configs',
          name: 'InspectionDbConfigs',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/DbConfigList'], resolve)
          }
        },
        {
          path: '/inspection/executions',
          name: 'InspectionExecutions',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/ExecutionList'], resolve)
          }
        },
        {
          path: '/inspection/execution/detail',
          name: 'InspectionExecutionDetail',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/ExecutionDetail'], resolve)
          }
        },
        {
          path: '/inspection/reports',
          name: 'InspectionReports',
          components: {
            Manage: (resolve) => require(['@/components/Inspection/Report'], resolve)
          }
        },
        {
          path: '/precise',
          redirect: '/precise/analysis'
        },
        {
          path: '/precise/analysis',
          name: 'PreciseAnalysisList',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/AnalysisList'], resolve)
          }
        },
        {
          path: '/precise/analysis/detail',
          name: 'PreciseAnalysisDetail',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/AnalysisDetail'], resolve)
          }
        },
        {
          path: '/precise/relations',
          name: 'PreciseRelationMap',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/RelationMap'], resolve)
          }
        },
        {
          path: '/precise/recommendation',
          name: 'PreciseRecommendation',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/Recommendation'], resolve)
          }
        },
        {
          path: '/precise/coverage',
          name: 'PreciseCoverageReport',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/CoverageReport'], resolve)
          }
        },
        {
          path: '/precise/coverage/detail',
          name: 'PreciseCoverageDetail',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/CoverageDetail'], resolve)
          }
        },
        {
          path: '/precise/gate',
          name: 'PreciseQualityGate',
          components: {
            Manage: (resolve) => require(['@/components/PreciseTest/QualityGate'], resolve)
          }
        },
        {
          path: '/bug',
          redirect: '/bug/list'
        },
        {
          path: '/bug/list',
          name: 'BugList',
          components: {
            Manage: (resolve) => require(['@/components/Bug/BugList'], resolve)
          }
        },
        {
          path: '/bug/detail',
          name: 'BugDetail',
          components: {
            Manage: (resolve) => require(['@/components/Bug/BugDetail'], resolve)
          }
        },
        {
          path: '/bug/create',
          name: 'BugCreate',
          components: {
            Manage: (resolve) => require(['@/components/Bug/BugEditor'], resolve)
          }
        },
        {
          path: '/bug/edit',
          name: 'BugEdit',
          components: {
            Manage: (resolve) => require(['@/components/Bug/BugEditor'], resolve)
          }
        },
        {
          path: '/bug/stats',
          name: 'BugStats',
          components: {
            Manage: (resolve) => require(['@/components/Bug/BugStats'], resolve)
          }
        },
        {
          path: '/data-tools/factory',
          name: 'BuilderList',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/DataFactory/BuilderList'], resolve)
          }
        },
        {
          path: '/data-tools/factory/editor',
          name: 'BuilderEditor',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/DataFactory/BuilderEditor'], resolve)
          }
        },
        {
          path: '/data-tools/factory/task',
          name: 'TaskHistory',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/DataFactory/TaskHistory'], resolve)
          }
        },
        {
          path: '/data-tools/factory/mock',
          name: 'MockService',
          components: {
            Manage: (resolve) => require(['@/components/TestPlatform/DataFactory/MockService'], resolve)
          }
        },
        {
          path: '/requirement-qa',
          name: 'RequirementQaList',
          components: {
            Manage: (resolve) => require(['@/components/RequirementQA/RequirementQaList'], resolve)
          }
        },
        {
          path: '/mock/document',
          name: 'MockDocumentList',
          components: {
            Manage: (resolve) => require(['@/components/Mock/MockDocumentList'], resolve)
          }
        },
        {
          path: '/mock/interface',
          name: 'MockInterfaceList',
          components: {
            Manage: (resolve) => require(['@/components/Mock/MockInterfaceList'], resolve)
          }
        },
        {
          path: '/mock/interface/detail',
          name: 'MockInterfaceDetail',
          components: {
            Manage: (resolve) => require(['@/components/Mock/MockInterfaceDetail'], resolve)
          }
        },
        {
          path: '/mock/log',
          name: 'MockLogList',
          components: {
            Manage: (resolve) => require(['@/components/Mock/MockLogList'], resolve)
          }
        },
        {
          path: '/system/role',
          name: 'RoleManage',
          components: {
            Manage: (resolve) => require(['@/components/System/RoleManage'], resolve)
          }
        },
        {
          path: '/system/user',
          name: 'UserManage',
          components: {
            Manage: (resolve) => require(['@/components/System/UserManage'], resolve)
          }
        },
        {
          path: '/system/menu',
          name: 'MenuManage',
          components: {
            Manage: (resolve) => require(['@/components/System/MenuManage'], resolve)
          }
        },
        {
          path: '/system/permission',
          name: 'PermissionManage',
          components: {
            Manage: (resolve) => require(['@/components/System/PermissionManage'], resolve)
          }
        }
      ]
    }
  ]
})
