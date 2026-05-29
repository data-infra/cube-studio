import { UserOutlined } from '@ant-design/icons';
import React from 'react';
import { IRouterConfigPlusItem } from './api/interface/baseInterface';
import { IAppMenuItem } from './api/interface/kubeflowInterface';
import Page404 from './pages/Page404';
import LoadingStar from './components/LoadingStar/LoadingStar';

const LoadingComponent = () => {
    return <div className="d-f ac jc w100 h100">
        <LoadingStar />
    </div>
}

const lazy2Compont = (factory: () => Promise<{
    default: () => JSX.Element;
}>, props?: any) => {
    const Component = React.lazy(() => factory())
    const id = Math.random().toString(36).substring(2)
    return <React.Suspense key={id} fallback={<LoadingComponent />}>
        <Component {...props} />
    </React.Suspense>
}

export const innerDynamicRouterConfig: IRouterConfigPlusItem[] = [
    {
        path: '/dataSearch',
        title: '数据查询',
        key: 'data_search',
        icon: '',
        menu_type: 'innerRouter',
        isCollapsed: true,
        element: lazy2Compont(() => import("./pages/DataSearch/DataSearch"))
    },
    {
        path: '/commonRelation',
        title: '通用关系图',
        element: lazy2Compont(() => import("./pages/CommonPipeline/DWStandard") as any)
    },
]

const innerDynamicRouterConfigMap = innerDynamicRouterConfig.reduce((pre, next) => ({
    ...pre,
    [next.key || '']: next
}), {}) as Record<string, IRouterConfigPlusItem>;

export const routerConfigPlus: IRouterConfigPlusItem[] = [
    {
        path: '/',
        index: true,
        element: lazy2Compont(() => import("./pages/Home/Home") as any)
    },
    {
        path: '/showData',
        title: '数据展示',
        element: lazy2Compont(() => import("./pages/ShowData"))
    },
    {
        path: '/showOutLink',
        title: '外链',
        element: lazy2Compont(() => import("./pages/IframeTemplate"))
    },
    ...innerDynamicRouterConfig,
    {
        path: '/user',
        icon: <UserOutlined style={{ fontSize: 18 }} />,
        element: lazy2Compont(() => import("./pages/UserCenter") as any)
    },
    { path: '*', element: <Page404 /> },
]

export const formatRoute = (data: IAppMenuItem[]): IRouterConfigPlusItem[] => {
    // console.log(data)
    const dfs = (data: IAppMenuItem[], chain?: IAppMenuItem[]): IRouterConfigPlusItem[] => {
        const res: IRouterConfigPlusItem[] = []
        for (let i = 0; i < data.length; i++) {
            const item = data[i];
            const currentChain = chain ? [...chain, item] : [item]
            const currentPath = currentChain.map(item => item.name)
            const routeProps = {
                isCollapsed: true,
                ...item,
                breadcrumbs: currentChain.map(item => item.title)
            }
            if (item.children?.length > 0) {
                res.push({
                    ...item,
                    path: `/${currentPath.join('/')}`,
                    children: dfs(item.children, currentChain),
                    // element: lazy2Compont(() => import("./pages/Home"), { ...routeProps }),
                })
            } else {
                const ADUGTemplateComponent = lazy2Compont(() => import("./pages/ADUGTemplate"), { ...routeProps, related: item.related })
                const OutLinkComponent = lazy2Compont(() => import("./pages/OutLinkTemplate"), { ...routeProps, related: item.related })
                const IframeComponent = lazy2Compont(() => import("./pages/IframeTemplate"), { ...routeProps, related: item.related })

                if (item.menu_type === 'out_link') {
                    res.push({
                        ...item,
                        path: `/${currentPath.join('/')}`,
                        element: OutLinkComponent
                    })
                } else if (item.menu_type === 'innerRoute') {
                    const page = innerDynamicRouterConfigMap[item.name]
                    res.push({
                        ...item,
                        path: `/${currentPath.join('/')}`,
                        element: page ? innerDynamicRouterConfigMap[item.name].element : ADUGTemplateComponent
                    })
                } else if (item.menu_type === 'iframe') {
                    res.push({
                        ...item,
                        path: `/${currentPath.join('/')}`,
                        element: IframeComponent
                    })
                } else {
                    res.push({
                        ...item,
                        path: `/${currentPath.join('/')}`,
                        element: ADUGTemplateComponent
                    })
                }

                if (item.related && item.related.length) {
                    for (let i = 0; i < item.related.length; i++) {
                        const relatedItem = item.related[i];
                        res.push({
                            ...relatedItem,
                            path: `/${currentPath.join('/')}/${relatedItem.name}`,
                            element: lazy2Compont(() => import("./pages/ADUGTemplate"), {
                                isCollapsed: true,
                                ...relatedItem,
                                isSubRoute: true,
                                model_name: item.model_name,
                                breadcrumbs: [...currentChain.map(item => item.title), relatedItem.title]
                            }),
                        })
                    }
                }
            }
        }
        return res
    }
    const resData = dfs(data)
    return resData
}

export const getDefaultOpenKeys = (data: IRouterConfigPlusItem[]) => {
    const openKeys: string[] = []
    const quene = [...data]
    while (quene.length) {
        const item = quene.shift()
        if (item?.isExpand && item.path) {
            openKeys.push(item.path)
        }
        if (item?.children && item.children[0]) {
            quene.push(...item.children)
        }
    }
    return openKeys
}
