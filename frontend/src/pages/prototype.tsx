import MoneyInput from '@/components/MoneyInput';
import Select from '../components/ResourceSelect';

import about from '../static/about';
import { colorPallete } from '@/styles/constants';
import Input from '@/components/Input';
import TransmissionCapSelect from '@/components/TransmissionCapSelect';
import YearSelect from '@/components/YearSelect';
import api from '../api';
import { useEffect, useState } from 'react';
import PercentLoader from '@/components/PercentLoader';

const Prototype = () => {
    const [ useApiData, setUseApiData ] = useState({
        wind: [],
        wave: [],
        kite: [],
        coaxial: [],
        transmission: ['Transmission/Transmission_300MW.npz'],
        max_system_radius: 30,
        lcoe_max: 120,
        lcoe_min: 100,
        lcoe_step: 2,
        start_year: 2007,
        end_year: 2007,
        max_wind: 1,
        min_wind: 1,
        max_kite: 1,
        min_kite: 1,
        max_wave: 0,
        min_wave: 0,
        max_coaxial: 0,
        min_coaxial: 0,
        WindTurbinesPerSite: 4,
        WindResolutionKm: 2,
        KiteTurbinesPerSite: 390, 
        WaveTurbinesPerSite: 300, 
        CoaxialTurbinesPerSite: 390
    });

    const [files, setFiles] = useState([]);

    const [ portfolio, setPortfolio ] = useState([]);

    const [ state, setState ] = useState({
        load: false,
        value: 0
    });

    const handleChange = (e:any) => {
        setFiles(Array.from(e.target.files));

        Array.from(e.target.files).forEach(item => {
            if(item.name.includes("PowerTimeSeriesKite")){
                const kite = useApiData.kite;
                kite.push("OceanCurrent/" + item.name);
                setUseApiData({...useApiData, kite: kite})
            }
        });
      };
    
    const handleUpload = async () => {
        if (!files || files.length === 0) return;

        const formData = new FormData();
        
        // Append files using the SAME key for all files
        files.forEach(file => {
            formData.append("files", file); // Key MUST match Flask's expected name
        });

        // Debugging: Verify FormData contents
        console.log("Files array:", files);
        for (const [key, value] of formData.entries()) {
            console.log(key, value);
          }

        const response = await api.resourceUpload(formData);

        console.log(response);
        // alert(data.message || "Upload complete!");
    }

    useEffect(() => {
        console.log(useApiData)
    }, [useApiData]);

    const handleWindDownload = async () => {
        if(useApiData.WindResolutionKm !== 2){
            const windInputGenerationApiData = {
                "WindTurbine": [],
                "ResolutionKm": useApiData.WindResolutionKm,
            };
            const windInputGenerationData = await api.generateWindBinaries(windInputGenerationApiData);
            console.log(windInputGenerationData);
    
            if (windInputGenerationData.status === 200){
                setState({load: true, value: 10})
            }
        }
        const windInputGenerationApiData = {
            "wind": useApiData.wind,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year
        };
        const windInputGenerationData = await api.windInputGeneration(windInputGenerationApiData);
        console.log(windInputGenerationData);

        if (windInputGenerationData.status === 200){
            setState({load: true, value: 30})
        }
    };

    const handleKiteDownload = async () => {
        const kiteInputGenerationApiData = {
            "kite": useApiData.kite,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year
        };
        const kiteInputGenerationData = await api.kiteInputGeneration(kiteInputGenerationApiData);
        console.log(kiteInputGenerationData);

        if (kiteInputGenerationData.status === 200){
            setState({load: true, value: 40})
        }
    };

    const handleWaveDownload = async () => {
        const waveInputGenerationApiData = {
            "wave": useApiData.wave,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year
        };
        const waveInputGenerationData = await api.waveInputGeneration(waveInputGenerationApiData);
        console.log(waveInputGenerationData);

        if (waveInputGenerationData.status === 200){
            setState({load: true, value: 50})
        }
    };

    const handleOnClick = async () => {
        await handleWindDownload();

        await handleKiteDownload();

        await handleWaveDownload();

        const data = await api.portfolioOptimization(useApiData);
        console.log(data);

        setPortfolio(data.data.save_path);
        return (data.data.save_path);
    };

    const postClickHandle = async (path: string) => {
        console.log(path)
        const response = await api.portfolioPlots({portfolio: path});
        console.log(response);

        const imageBlob = new Blob([response.data], { type: 'image/png' });
        const imageURL = URL.createObjectURL(imageBlob);
        console.log(imageURL);
        document.getElementById('image').src = imageURL;
    };

    useEffect(() => {
        console.log(state);
    }, [state]);
    return (
        <div className='w-2/3 lg:w-1/3 flex flex-col items-center justify-center'>
            {state.load === true ? <div>
                <div className='w-full'>
                    <span className="self-center text-xl mt-5 mb-5 whitespace-nowrap align-middle h-full m-2">Loading: {state.value}%</span>
                    <PercentLoader width={state.value}/>
                </div>
            </div> : 
            (<div className='w-full flex flex-col justify-items-start items-start'>
            <span className="self-center text-4xl mt-5 mb-5 whitespace-nowrap align-middle h-full">Portfolio Optimization</span>
                <div className='m-3 mb-8 w-full'>
                    <p className="mb-3 not-italic underline decoration-4 underline-offset-4" style={{ textDecorationColor: colorPallete.primary }}>Resources</p>
                    <Select state={useApiData} setState={setUseApiData} />
                    <div>
                        <label
                            className="block mt-4 mb-2 text-sm font-medium text-gray-900 dark:text-white"
                            htmlFor="multiple_files"
                        >
                            Upload multiple files
                        </label>
                        <input
                            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400"
                            id="multiple_files"
                            type="file"
                            multiple
                            onChange={handleChange}
                        />
                        <button
                            className="inline-flex items-center w-full justify-center mt-3 px-3 py-2 text-sm font-medium text-center text-white rounded-lg hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300" style={{
                                backgroundColor: colorPallete.primary
                            }}
                            onClick={handleUpload}
                        >
                            Upload
                        </button>
                        {/* Optional: Show selected files */}
                        <ul className="mt-2">
                            {files.map((file, i) => (
                            <li key={i}>{file.name}</li>
                            ))}
                        </ul>
                    </div>
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
                        <TransmissionCapSelect state={useApiData} setState={setUseApiData}/>
                        <Input label='Max Trans. System Radius' type='number' step="0.01" placeholder='30' curr='mi' state={useApiData} setState={setUseApiData}/>
                        {useApiData.wind.length > 0 && (<Input label='Number of Wind Devices / Resource' type='number' step="1" placeholder='4' curr='' state={useApiData} setState={setUseApiData}/>)}
                        {useApiData.wind.length > 0 && (<Input label='Number of Wind Devices / sq. km' step="1" type='number' placeholder='2' curr='' state={useApiData} setState={setUseApiData}/>)}

                        {useApiData.kite.length > 0 && (<Input label='Number of Kite Devices / Resource' type='number' step="1" placeholder='390' curr='' state={useApiData} setState={setUseApiData}/>)}
                        {useApiData.kite.length > 0 && (<Input label='Number of Kite Devices / sq. km' step="1" type='number' placeholder='0' curr='' state={useApiData} setState={setUseApiData}/>)}

                        {useApiData.wave.length > 0 && (<Input label='Number of Wave Devices / Resource' type='number' step="1" placeholder='300' curr='' state={useApiData} setState={setUseApiData}/>)}
                        {useApiData.wave.length > 0 && (<Input label='Number of Wave Devices / sq. km' step="1" type='number' placeholder='0' curr='' state={useApiData} setState={setUseApiData}/>)}

                        {useApiData.coaxial.length > 0 && (<Input label='Number of Coaxial Devices / Resource' type='number' step="1" placeholder='390' curr='' state={useApiData} setState={setUseApiData}/>)}
                        {useApiData.coaxial.length > 0 && (<Input label='Number of Coaxial Devices / sq. km' step="1" type='number' placeholder='0' curr='' state={useApiData} setState={setUseApiData}/>)}

                        {/* <Input label='Year(s) of Analysis' type='number' step="1" placeholder='0' curr=''/> */}
                        <YearSelect label='Year(s) of Analysis from' state={useApiData} setState={setUseApiData} start={true} />
                        <YearSelect label='Year(s) of Analysis to' state={useApiData} setState={setUseApiData} start={false} />
                        <Input label='Distance from Shore' step="0.01" type='number' placeholder='0.0' curr='mi' state={useApiData} setState={setUseApiData}/>
                        <Input label='Max Water Depth' type='number' step="0.01" placeholder='0.0' curr='mi'state={useApiData} setState={setUseApiData}/>
                        
                        <Input label='LCOE Min' type='number' step="1" placeholder='100' curr='$/MWh' state={useApiData} setState={setUseApiData}/>
                        <Input label='LCOE Max' type='number' step="1" placeholder='120' curr='$/MWh'state={useApiData} setState={setUseApiData}/>
                        <Input label='LCOE Step Size' type='number' step="1" placeholder='2' curr='' state={useApiData} setState={setUseApiData}/>
                    </div>
                </div>
                <button onClick={async () => {
                    setState({load: true, value: 0})
                    const path = await handleOnClick();
                    setState({load: false, value: 100})
                    await postClickHandle(path);
                }} className="inline-flex items-center w-full justify-center m-3 mt-8 px-3 py-2 text-sm font-medium text-center text-white rounded-lg hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300" style={{
                    backgroundColor: colorPallete.primary
                }}>Generate Efficient Frontiers</button>
            </div>)
            }
            <img id='image' className='w-full h-full' />
        </div>
    );
};

export default Prototype;