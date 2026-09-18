/**
 * 真实数据测试脚本
 * 验证从天天基金网获取真实基金数据
 */

const FundDataFetcher = require('./data-fetcher');

async function testDataFetcher() {
    const fetcher = new FundDataFetcher();
    
    console.log('========================================');
    console.log('  基金数据采集测试 - 真实数据验证');
    console.log('========================================\n');
    
    // 测试基金列表
    const testFunds = [
        '110011',  // 易方达中小盘混合
        '161725',  // 招商中证白酒指数
        '005827',  // 易方达蓝筹精选混合
        '003834',  // 华夏能源革新股票
        '005267'   // 嘉实核心优势股票
    ];
    
    console.log('1. 测试获取基金实时估值...\n');
    
    for (const fundCode of testFunds) {
        try {
            const estimate = await fetcher.getRealTimeEstimate(fundCode);
            if (estimate) {
                console.log(`✓ ${fundCode} - ${estimate.fund_name}`);
                console.log(`  最新净值: ¥${estimate.last_nav}`);
                console.log(`  估算净值: ¥${estimate.estimate_nav}`);
                console.log(`  估算涨幅: ${estimate.estimate_return}%`);
                console.log(`  数据时间: ${estimate.last_date}\n`);
            } else {
                console.log(`✗ ${fundCode} - 获取失败\n`);
            }
        } catch (error) {
            console.log(`✗ ${fundCode} - 错误: ${error.message}\n`);
        }
        
        // 延迟，避免请求过快
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    console.log('2. 测试获取历史净值数据...\n');
    
    const sampleFund = '110011';
    try {
        // 获取最近30天数据
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        
        console.log(`获取 ${sampleFund} 最近30天净值数据...`);
        const navData = await fetcher.getNavHistory(sampleFund, startDate, endDate);
        
        if (navData && navData.length > 0) {
            console.log(`✓ 成功获取 ${navData.length} 条净值数据\n`);
            console.log('最新5条数据:');
            navData.slice(0, 5).forEach(nav => {
                console.log(`  ${nav.nav_date}: ¥${nav.unit_nav} (${nav.daily_return}%)`);
            });
        } else {
            console.log('✗ 未获取到历史数据\n');
        }
    } catch (error) {
        console.log(`✗ 获取历史数据失败: ${error.message}\n`);
    }
    
    console.log('\n========================================');
    console.log('  测试完成');
    console.log('========================================');
    
    fetcher.close();
}

// 运行测试
testDataFetcher().catch(console.error);