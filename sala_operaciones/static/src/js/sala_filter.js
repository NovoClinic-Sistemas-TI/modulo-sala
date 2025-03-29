/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class SalaFilter extends Component {
    static template = "sala_operaciones.SalaFilter";
    
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({ salas: [] });
        
        onWillStart(async () => {
            await this.loadSalas();
        });
    }

    async loadSalas() {
        try {
            const response = await this.rpc("/sala_operaciones/get_salas");
            this.state.salas = response.data.map(sala => ({
                id: sala.id,
                name: sala.nombre, 
                color: sala.color || "#FFE0E0"
            }));
        } catch (error) {
            console.error("Error:", error);
        }
    }

    toggleFilter(salaId) {
        const searchModel = this.env.searchModel;
        if (searchModel) {
            searchModel.setDomainParts({
                sala_filter: {
                    domain: [["sala_operaciones_id", "=", salaId]],
                    active: true
                }
            });
        }
    }
}

// Registrar como Widget del Sidebar del Calendario
registry.category("calendar_sidebar").add("SalaFilter", SalaFilter, {
    sequence: 10, // Prioridad alta para aparecer primero
    shouldBeDisplayed: (env) => env.model === 'surgery.reservation' // Solo en tu modelo
});