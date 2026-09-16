"""
Farm Wise AI – Government Schemes Routes
"""

from flask import Blueprint, render_template, request
from models import db, GovernmentScheme

schemes_bp = Blueprint("schemes", __name__, url_prefix="/schemes")

SAMPLE_SCHEMES = [
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Direct income support of ₹6,000 per year to all farmer families across the country in three equal installments of ₹2,000 each every four months.",
        "eligibility": "Small and marginal farmers with cultivable land up to 2 hectares. All farmer families regardless of the size of their landholding.",
        "benefits": "₹6,000 per year direct bank transfer in 3 installments",
        "documents_required": "Aadhaar Card, Land Records/Khasra-Khatauni, Bank Account Details, Mobile Number",
        "application_link": "https://pmkisan.gov.in",
        "deadline": "Ongoing – Apply anytime",
        "category": "subsidy",
        "state": "All India",
    },
    {
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Comprehensive crop insurance scheme covering pre-sowing to post-harvest losses due to natural calamities, pests, and diseases.",
        "eligibility": "All farmers growing notified crops. Loanee farmers are mandatorily covered. Non-loanee farmers can voluntarily enroll.",
        "benefits": "Crop insurance coverage up to sum insured. Premium: 2% for Kharif, 1.5% for Rabi, 5% for commercial crops",
        "documents_required": "Land Records, Aadhaar, Bank Passbook, Sowing Certificate",
        "application_link": "https://pmfby.gov.in",
        "deadline": "Before crop sowing (seasonal)",
        "category": "insurance",
        "state": "All India",
    },
    {
        "name": "Kisan Credit Card (KCC)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Provides adequate and timely credit to farmers for crop cultivation, allied activities and non-farm activities at low interest rates.",
        "eligibility": "All farmers, tenant farmers, oral lessees, sharecroppers, and SHG/JLG members",
        "benefits": "Credit limit up to ₹3 lakh at 7% interest rate (4% after subsidy). No collateral up to ₹1.6 lakh.",
        "documents_required": "Land Records, Aadhaar, PAN Card, Passport Photos, Bank Account",
        "application_link": "https://www.nabard.org/kcc",
        "deadline": "Ongoing – Apply at nearest bank",
        "category": "loan",
        "state": "All India",
    },
    {
        "name": "Soil Health Card Scheme",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Provides every farmer a soil health card with information on soil nutrients status and fertilizer recommendations for 12 major parameters.",
        "eligibility": "All farmers. Cards issued once in 3 years per farm holding.",
        "benefits": "Free soil testing. Recommendations for NPK and micronutrients. Potential savings of 8-10% on fertilizer costs.",
        "documents_required": "Aadhaar Card, Land ownership proof",
        "application_link": "https://soilhealth.dac.gov.in",
        "deadline": "Ongoing",
        "category": "subsidy",
        "state": "All India",
    },
    {
        "name": "PM Krishi Sinchayee Yojana (PMKSY)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Aimed at ensuring access to water for every agricultural field (Har Khet Ko Pani) and improving water use efficiency (More Crop Per Drop).",
        "eligibility": "All farmers. Priority to small and marginal farmers and SC/ST farmers",
        "benefits": "Subsidy on micro-irrigation: 55% for small/marginal farmers, 45% for others. Pipeline subsidy, sprinkler subsidy.",
        "documents_required": "Land Records, Aadhaar, Bank Account, Quotation from certified dealer",
        "application_link": "https://pmksy.gov.in",
        "deadline": "Ongoing – apply at district agriculture office",
        "category": "subsidy",
        "state": "All India",
    },
    {
        "name": "eNAM (Electronic National Agriculture Market)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Pan-India electronic trading portal for agricultural commodities. Enables online price discovery and transparent marketing.",
        "eligibility": "All farmers and FPOs. Available in 1000+ mandis across 18 states.",
        "benefits": "Better price realization, reduced transportation costs, transparent bidding, real-time market data",
        "documents_required": "Aadhaar, Bank Account, Mobile Number, Commodity quality certificate",
        "application_link": "https://enam.gov.in",
        "deadline": "Ongoing registration",
        "category": "training",
        "state": "All India",
    },
    {
        "name": "National Food Security Mission (NFSM)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Aims to increase production of rice, wheat, pulses, coarse cereals and nutri-cereals through area expansion and productivity enhancement.",
        "eligibility": "Farmers in targeted districts for rice, wheat, pulses. Priority to small and marginal farmers.",
        "benefits": "Subsidized seeds, INM/IPM demonstrations, farm machinery subsidy, training programs",
        "documents_required": "Land Records, Aadhaar, Bank Account",
        "application_link": "https://nfsm.gov.in",
        "deadline": "Seasonal – Check district agriculture office",
        "category": "subsidy",
        "state": "All India",
    },
    {
        "name": "Paramparagat Krishi Vikas Yojana (PKVY)",
        "ministry": "Ministry of Agriculture & Farmers Welfare",
        "description": "Promotes traditional and organic farming practices to improve soil health and provide farmers with premium prices for organic produce.",
        "eligibility": "Farmers willing to adopt organic farming. Must form clusters of 50 farmers on 50 acres",
        "benefits": "₹50,000 per hectare over 3 years for conversion to organic farming. Training, certification, marketing support.",
        "documents_required": "Land Records, Aadhaar, Group formation certificate, Soil Test Report",
        "application_link": "https://pgsindia-ncof.gov.in",
        "deadline": "Apply before Kharif/Rabi season start",
        "category": "subsidy",
        "state": "All India",
    },
]


def init_schemes():
    """Seed government schemes if DB is empty."""
    if GovernmentScheme.query.count() == 0:
        for s in SAMPLE_SCHEMES:
            scheme = GovernmentScheme(**s)
            db.session.add(scheme)
        db.session.commit()


@schemes_bp.route("/")
def index():
    search = request.args.get("search", "")
    category = request.args.get("category", "all")
    state = request.args.get("state", "All India")
    page = request.args.get("page", 1, type=int)

    query = GovernmentScheme.query.filter_by(is_active=True)
    if search:
        query = query.filter(GovernmentScheme.name.ilike(f"%{search}%"))
    if category != "all":
        query = query.filter_by(category=category)

    schemes = query.paginate(page=page, per_page=6, error_out=False)
    categories = ["all", "subsidy", "loan", "insurance", "training"]

    return render_template(
        "schemes/index.html",
        schemes=schemes,
        categories=categories,
        current_category=category,
        search=search,
        sample_schemes=SAMPLE_SCHEMES,
    )
