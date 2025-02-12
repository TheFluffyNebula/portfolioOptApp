import axios from "axios";
import React, { useContext, useState } from "react";

const url = "http://localhost:4000";

const api = {
    test: async () => {
        const data = await axios.post(
            `${url}/test`,
            {
                method: "POST",
                headers: {
                    'Content-type': 'application-json',
                    'Access-Control-Allow-Origin': '*',
                },
            }
        );
        return data;
    },
    generateEfficientFrontiers: async (
        resourceType,
        transmission,
        lcoe_max=120,
        lcoe_min=100,
        lcoe_step=4,
    ) => {
        const dataObj = {
            resourceType,
            transmission,
            lcoe_max,
            lcoe_min,
            lcoe_step
        };
        const data = await axios.post(
            `${url}/generate`,
            {
                method: "POST",
                headers: {
                    'Content-type': 'application-json',
                    'Access-Control-Allow-Origin': '*',
                },
                body: JSON.stringify(dataObj)
            }
        );
        return data;
    },
};

export default api;