import React from 'react';

interface InputProps {
    label: string;
    type: string;
    placeholder: string;
    curr: string;
    step: string;
    state: {
        wind: string[],
        wave: string[],
        kite: string[],
        transmission: string[],
        lcoe_max: number,
        lcoe_min: number,
        lcoe_step: number,
        start_year: number,
        end_year: number,
      };
      setState: any;
};


const Input = (props: InputProps) => {
    const onChangeHandler = (event) => {
        if (props.label == "LCOE Min")
        props.setState({...props.state, lcoe_min: parseInt(event.target.value)});

        if (props.label == "LCOE Max")
            props.setState({...props.state, lcoe_max: parseInt(event.target.value)});

        if (props.label == "LCOE Step Size")
            props.setState({...props.state, lcoe_step: parseInt(event.target.value)});
        if (props.label == 'Max Trans. System Radius')
            props.setState({...props.state, max_system_radius: parseInt(event.target.value)});
        if (props.label == 'Number of Wind Devices / Resource')
            props.setState({...props.state, WindTurbinesPerSite: parseInt(event.target.value)});
        if (props.label == 'Number of Wind Devices / sq. km')
            props.setState({...props.state, WindResolutionKm: parseInt(event.target.value)});

        if (props.label == 'Number of Wave Devices / Resource')
            props.setState({...props.state, WaveTurbinesPerSite: parseInt(event.target.value)});

        if (props.label == 'Number of Kite Devices / Resource')
            props.setState({...props.state, KiteTurbinesPerSite: parseInt(event.target.value)});

        if (props.label == 'Number of Coaxial Devices / Resource')
            props.setState({...props.state, CoaxialTurbinesPerSite: parseInt(event.target.value)});
    };
    return (
        <div>
            <label htmlFor="price" className="block text-sm/6 font-medium text-gray-900">
                {props.label}
            </label>
            <div className="mt-2">
                <div className="flex items-center rounded-md bg-white pl-3 outline-1 -outline-offset-1 outline-gray-300 has-[input:focus-within]:outline-2 has-[input:focus-within]:-outline-offset-2 has-[input:focus-within]:outline-indigo-600">
                    <input
                        id="price"
                        name="price"
                        type={props.type}
                        step={props.step}
                        placeholder={props.placeholder}
                        onChange={onChangeHandler}
                        className="block min-w-0 grow py-1.5 pr-3 pl-1 text-base text-gray-900 placeholder:text-gray-400 focus:outline-none sm:text-sm/6 rounded-md"
                    />
                    <div className="grid shrink-1 grid-cols-1 focus-within:relative">
                        <div className="col-start-1 row-start-1 w-full appearance-none rounded-md py-1.5 pr-7 pl-3 text-base text-gray-500 placeholder:text-gray-400 focus:outline-2 focus:-outline-offset-2 focus:outline-indigo-600 sm:text-sm/6">
                            {props.curr}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Input;