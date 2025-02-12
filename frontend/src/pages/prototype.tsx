import MoneyInput from '@/components/MoneyInput';
import Select from '../components/ResourceSelect';

import about from '../static/about';
import { colorPallete } from '@/styles/constants';
import Input from '@/components/Input';
import TransmissionCapSelect from '@/components/TransmissionCapSelect';
import YearSelect from '@/components/YearSelect';
import api from '../api';

const Prototype = () => {
    const handleOnClick = async () => {
        // const data = await api.test();
        // console.log(data);

        const data = await api.generateEfficientFrontiers(
            ['Wind/Upscale3h_0.1Degree_2007_2013_GenCost_ATB_8MW_2020_Vestas.npz'], 
            ['Transmission/Transmission_1200MW.npz'],
            120,
            100,
            4
        );

        console.log(data);
    };
    return (
        <div className='w-2/3 lg:w-1/3 flex flex-col items-center'>
            <div className='w-full flex flex-col justify-items-start items-start'>
            <span className="self-center text-4xl mt-5 mb-5 whitespace-nowrap align-middle h-full">Portfolio Optimization</span>
                <div className='m-3 mb-8 w-full'>
                    <p className="mb-3 not-italic underline decoration-4 underline-offset-4" style={{ textDecorationColor: colorPallete.primary }}>Resources</p>
                    <Select />
                </div>

                <div className='m-3 mb-8 w-full'>
                <p className="mb-3 not-italic underline decoration-4 underline-offset-4" style={{ textDecorationColor: colorPallete.primary }}>Location</p>
                    <div className='grid grid-cols-2 gap-6 justify-center'>
                        <Input label='Latitude Start' step="0.01" type='number' placeholder='0' curr='deg'/>
                        <Input label='Latitude End' step="0.01" type='number' placeholder='0' curr='deg'/>
                        <Input label='Longitude Start' type='number' step="0.01" placeholder='0' curr='deg'/>
                        <Input label='Longitude End' type='number' step="0.01" placeholder='0' curr='deg'/>
                    </div>
                </div>

                <div className='m-3 w-full'>
                <p className="mb-3 not-italic underline decoration-4 underline-offset-4" style={{ textDecorationColor: colorPallete.primary }}>Technicals</p>
                    <div className='grid grid-cols-2 gap-6 justify-center'>
                        <TransmissionCapSelect />
                        <Input label='Max Trans. System Radius' type='number' step="0.01" placeholder='0' curr='mi'/>
                        <Input label='Number of Devices / Resource' type='number' step="1" placeholder='0.0' curr=''/>
                        <Input label='Number of Devices / sq. km' step="1" type='number' placeholder='0' curr=''/>
                        {/* <Input label='Year(s) of Analysis' type='number' step="1" placeholder='0' curr=''/> */}
                        <YearSelect label='Year(s) of Analysis from'/>
                        <YearSelect label='Year(s) of Analysis to'/>
                        <Input label='Distance from Shore' step="0.01" type='number' placeholder='0.0' curr='mi' />
                        <Input label='Max Water Depth' type='number' step="0.01" placeholder='0.0' curr='mi'/>
                        <Input label='Wind Speed Diameter' type='number' step="1" placeholder='0' curr='mi'/>
                        <Input label='LCOE Step Size' type='number' step="1" placeholder='4' curr=''/>
                        <Input label='LCOE Min' type='number' step="1" placeholder='30' curr='$/MWh'/>
                        <Input label='LCOE Max' type='number' step="1" placeholder='120' curr='$/MWh'/>
                    </div>
                </div>
                <button onClick={handleOnClick} className="inline-flex items-center w-full justify-center m-3 mt-8 px-3 py-2 text-sm font-medium text-center text-white rounded-lg hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300" style={{
                    backgroundColor: colorPallete.primary
                }}>Generate Efficient Frontiers</button>
            </div>
        </div>
    );
};

export default Prototype;