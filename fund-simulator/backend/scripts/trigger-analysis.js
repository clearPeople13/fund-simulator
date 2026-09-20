/**
 * 触发AI分析脚本
 * 手动触发交易分析团队进行基金分析
 */

const axios = require('axios');

async function triggerAIAnalysis() {
    console.log('========================================');
    console.log('  触发AI分析 - 交易分析团队');
    console.log('========================================\n');
    
    const fundCodes = ['110011', '161725', '003834', '005827', '005267'];
    
    console.log('准备分析以下基金:');
    fundCodes.forEach(code => console.log(`  - ${code}`));
    console.log('');
    
    try {
        console.log('正在触发AI分析...\n');
        
        const response = await axios.post('http://localhost:3000/api/ai/analyze', {
            fund_codes: fundCodes
        });
        
        console.log('✓ AI分析已触发\n');
        console.log('分析结果:');
        console.log(JSON.stringify(response.data, null, 2));
        
    } catch (error) {
        console.error('✗ 触发AI分析失败:', error.message);
    }
}

// 运行
triggerAIAnalysis();